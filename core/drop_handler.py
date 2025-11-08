"""
Drop Handler Module
===================

Mục đích:
    Module này xử lý tất cả logic liên quan đến drop items từ game:
    - Phát hiện khi vào/ra map
    - Xử lý và thống kê các items rơi ra
    - Tính toán giá trị và ghi vào file log/drop.txt

Tác dụng:
    - Theo dõi trạng thái vào/ra map
    - Parse và xử lý drop items từ log
    - Cập nhật statistics (drop_list, income, etc.)
    - Ghi log drops vào file log/drop.txt để theo dõi

Các function chính:
    - deal_drop(): Xử lý drop data và cập nhật statistics
    - deal_change(): Phát hiện map changes và trigger drop processing

Global variables:
    - drop_list: Dictionary lưu drops của map hiện tại
    - drop_list_all: Dictionary lưu tất cả drops
    - income: Giá trị items map hiện tại
    - income_all: Tổng giá trị items
    - pending_items: Queue các items chưa có trong local database
"""
import time
import json
import os
from datetime import datetime
from .log_parser import convert_from_log_structure, scanned_log
from .logger import log_debug
from services.log_scan_service import scan_drop_log, scan_init_bag
from app import state


# Global state variables (will be initialized in main)
pending_items = {}
exclude_list = []
drop_list = {}
drop_list_all = {}
income = 0
income_all = 0
config_data = {}
# Track số lượng items trước đó trong map (để tính chênh lệch khi nhặt)
previous_item_quantities = {}  # {item_id: quantity}


def deal_drop(drop_data, item_id_table, price_table):
    """Update drop statistics"""
    global income, income_all, drop_list, drop_list_all, config_data, pending_items, exclude_list
    
    def invoke_drop_item_processing(item_data, item_key):
        """
        Xử lý một drop item đơn lẻ từ parsed log data (format cũ)
        
        Flow xử lý:
        1. Kiểm tra item đã được nhặt (Picked flag)
        2. Extract BaseId và Num từ item_data (có thể từ SpecialInfo)
        3. Convert item ID sang name từ item_id_table
        4. Nếu không có trong local, thêm vào pending_items queue
        5. Kiểm tra exclude list
        6. Cập nhật drop_list và drop_list_all
        7. Tính giá và cập nhật income
        8. Ghi log vào log/drop.txt
        
        Args:
            item_data (dict): Dictionary chứa thông tin item từ parsed log
            item_key (str): Key/path của item trong nested structure
        
        Note:
            - Function này xử lý format log cũ (có thể không còn được dùng)
            - Format mới sử dụng scan_drop_log() trong deal_change()
        """
        global income, income_all, drop_list, drop_list_all, exclude_list, pending_items, config_data
        
        # Check if picked (Picked may be at root level or inside item)
        picked = False
        print(item_data)
        if "Picked" in item_data:
            picked = item_data["Picked"]
        elif isinstance(item_data.get("item"), dict) and "Picked" in item_data["item"]:
            picked = item_data["item"]["Picked"]

        if not picked:
            return

        # Process SpecialInfo (nested item information)
        # SpecialInfo có thể chứa BaseId và Num thực tế của item
        item_info = item_data.get("item", {})
        if isinstance(item_info, dict) and "SpecialInfo" in item_info:
            special_info = item_info["SpecialInfo"]
            if isinstance(special_info, dict):
                if "BaseId" in special_info:
                    item_info["BaseId"] = special_info["BaseId"]
                if "Num" in special_info:
                    item_info["Num"] = special_info["Num"]

        # Get base ID and quantity
        base_id = item_info.get("BaseId")
        num = item_info.get("Num", 0)

        if base_id is None:
            return

        # Convert ID to name
        base_id_str = str(base_id)
        
        # Log khi nhặt được item
        log_debug(f"drop item {base_id_str}")
        item_name = base_id_str  # Default to using ID as name

        # Lấy name từ item_id_table, nếu không có thì thêm vào pending queue
        if base_id_str in item_id_table:
            item_name = item_id_table[base_id_str]
        else:
            # No local data, add to pending queue để fetch từ server sau
            global pending_items
            if base_id_str not in pending_items:
                print(f"[Network] ID {base_id_str} not found locally, starting fetch")
                pending_items[base_id_str] = num
            else:
                pending_items[base_id_str] += num
                print(f"[Network] ID {base_id_str} already in queue, accumulated: {pending_items[base_id_str]}")
            return

        # Check if item name is empty
        if not item_name.strip():
            return

        # Check if in exclude list (items không muốn track)
        global exclude_list
        if exclude_list and item_name in exclude_list:
            print(f"Excluded: {item_name} x{num}")
            return
        print(base_id)
        
        # Count quantity: Cập nhật drop_list (map hiện tại) và drop_list_all (tổng)
        if base_id not in drop_list:
            drop_list[base_id] = 0
        drop_list[base_id] += num

        if base_id not in drop_list_all:
            drop_list_all[base_id] = 0
        drop_list_all[base_id] += num

        # Calculate price: Lấy giá từ price_table, áp dụng tax nếu có
        price = 0.0
        if str(base_id) in price_table:
            base_id = str(base_id)
            price = price_table[base_id]
            if config_data.get("tax", 0) == 1 and base_id != "100300":
                price = price * 0.875  # Tax 12.5%
            income += price * num
            income_all += price * num

        log_debug(f"drop item {item_name} x{num} ({round(price, 3)}/each)")
        # Record to file: Ghi log vào log/drop.txt
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] Drop: {item_name} x{num} ({round(price, 3)}/each)\n"
        drop_log_path = os.path.join("log", "drop.txt")
        os.makedirs("log", exist_ok=True)
        with open(drop_log_path, "a", encoding="utf-8") as f:
            f.write(log_line)

    def invoke_drop_items_recursive(data, path=""):
        """
        Recursively scan và xử lý tất cả dropped items từ nested dictionary structure
        
        Flow:
        1. Duyệt qua tất cả keys trong dictionary
        2. Tìm các node có chứa "item" key (có thể là drop item)
        3. Kiểm tra có "Picked" marker không (đã nhặt)
        4. Nếu có Picked, gọi invoke_drop_item_processing() để xử lý
        5. Tiếp tục đệ quy vào các child nodes để tìm items khác
        
        Args:
            data (dict): Nested dictionary chứa drop items structure từ parsed log
            path (str): Current path trong nested structure (dùng để debug/tracking)
        
        Note:
            - Function này duyệt recursive qua toàn bộ nested structure
            - Chỉ xử lý items có "Picked" = True (đã nhặt)
            - Format log cũ sử dụng nested structure với "item" và "Picked" markers
        """
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            # Check if contains drop data: Tìm node có chứa "item" key
            if isinstance(value, dict) and "item" in value:
                # Check if has Picked marker: Kiểm tra item đã được nhặt chưa
                # Picked có thể ở root level hoặc trong item dict
                has_picked = ("Picked" in value) or \
                             (isinstance(value["item"], dict) and "Picked" in value["item"])

                if has_picked:
                    # Item đã được nhặt, xử lý nó
                    invoke_drop_item_processing(value, current_path)

            # Recursively process child items: Tiếp tục đệ quy vào các child nodes
            if isinstance(value, dict):
                invoke_drop_items_recursive(value, current_path)

    # Start recursive processing
    invoke_drop_items_recursive(drop_data)


def deal_change(changed_text):
    """
    Xử lý thay đổi trong log file: phát hiện vào/ra map và xử lý drops
    
    Tác dụng chính:
    1. Phát hiện vào/ra map: Cập nhật is_in_map, reset drop_list, tính chi phí map
    2. Load dữ liệu items: Đọc id_table.json (name, type) và search_price_log.json (price)
    3. Scan và parse drops: Tìm drop blocks trong log, parse thành JSON
    4. Xử lý drops: Cập nhật drop_list, income, ghi vào log/drop.txt
    6. Tính profit: Ghi profit vào log/profit_log.json khi ra map
    5. Cập nhật UI: Refresh UI khi có drops mới
    
    Args:
        changed_text (str): Nội dung log mới được đọc từ file
    
    Note: This function uses state from app.state module, không import index để tránh circular import
    """
    global drop_list, income, drop_list_all, income_all, config_data, previous_item_quantities
    
    # Detect map entry
    if "PageApplyBase@ _UpdateGameEnd: LastSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200/XZ_YuJinZhiXiBiNanSuo200.XZ_YuJinZhiXiBiNanSuo200' NextSceneName = World'/Game/Art/Maps" in changed_text:
        state.is_in_map = True
        drop_list = {}
        previous_item_quantities = {}  # Reset tracking khi vào map mới
        
        # Tính chi phí map và trừ vào income
        map_cost = state.root.cost if state.root else 0
        income = -map_cost
        income_all += -map_cost
        state.map_count += 1
        
        # Lưu thời gian bắt đầu map để tính duration
        state.map_start_time = time.time()
        
    # Detect map exit
    if "NextSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200/XZ_YuJinZhiXiBiNanSuo200.XZ_YuJinZhiXiBiNanSuo200'" in changed_text:
        state.is_in_map = False
        map_duration = time.time() - state.t
        state.total_time += map_duration
        
        # Tính profit và ghi vào profit_log.json
        # Profit = income (đã bao gồm cả cost được trừ khi vào map)
        map_cost = state.root.cost if state.root else 0
        map_profit = income  # income đã là profit (income - cost)
        
        # Ghi marker "END MAP" vào log/drop_log.txt và log/drop.txt
        try:
            os.makedirs("log", exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            end_map_marker = f"\n==========================END MAP================\n"
            
            # Ghi vào log/drop_log.txt
            drop_log_path = os.path.join("log", "drop_log.txt")
            with open(drop_log_path, "a", encoding="utf-8") as f:
                f.write(end_map_marker)
            
            # Ghi vào log/drop.txt
            drop_txt_path = os.path.join("log", "drop.txt")
            with open(drop_txt_path, "a", encoding="utf-8") as f:
                f.write(end_map_marker)
        except Exception as e:
            log_debug(f"error writing END MAP marker: {e}")
        
        # Ghi profit log
        try:
            profit_log_path = os.path.join("log", "profit_log.json")
            os.makedirs("log", exist_ok=True)
            
            # Đọc profit log hiện tại hoặc tạo mới
            try:
                with open(profit_log_path, 'r', encoding="utf-8") as f:
                    profit_log = json.load(f)
            except FileNotFoundError:
                profit_log = []
            
            # Tạo entry mới
            profit_entry = {
                "timestamp": round(time.time()),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "map_count": state.map_count,
                "income": round(income, 2),
                "cost": round(map_cost, 2),
                "profit": round(map_profit, 2),
                "duration_seconds": round(map_duration, 2),
                "duration_formatted": f"{int(map_duration // 60)}m{int(map_duration % 60)}s"
            }
            
            profit_log.append(profit_entry)
            
            # Ghi lại file
            with open(profit_log_path, 'w', encoding="utf-8") as f:
                json.dump(profit_log, f, indent=4, ensure_ascii=False)
            
            log_debug(f"profit logged: map #{state.map_count}, profit={round(map_profit, 2)}, duration={round(map_duration, 2)}s")
        except Exception as e:
            log_debug(f"error writing to profit_log.json: {e}")
    
    # Load item ID and price tables từ id_table.json và search_price_log.json
    id_table = {}
    price_table = {}
    
    # Load id_table.json để lấy name và type
    try:
        with open("id_table.json", 'r', encoding="utf-8") as f:
            id_table_data = json.load(f)
        for item_id, item_data in id_table_data.items():
            id_table[str(item_id)] = item_data.get("name", f"Item {item_id}")
    except Exception as e:
        log_debug(f"error reading id_table.json: {e}")
    
    # Load search_price_log.json để lấy price
    try:
        with open("search_price_log.json", 'r', encoding="utf-8") as f:
            price_log = json.load(f)
        for entry in price_log:
            item_id = entry.get("idItem")
            price = entry.get("price", 0)
            if item_id:
                price_table[str(item_id)] = price
    except Exception as e:
        log_debug(f"error reading search_price_log.json: {e}")
    
    # Scan init bag trước để lấy số lượng items hiện tại trong túi
    init_bag_data = scan_init_bag(changed_text)
    if init_bag_data:
        # Cập nhật previous_item_quantities từ init bag data
        for item_id_str, bag_info in init_bag_data.items():
            item_id_int = int(item_id_str)
            previous_item_quantities[item_id_int] = bag_info.get("num", 0)
    
    # Scan drops từ log theo format mới (PickItems)
    # Truyền id_table và price_table để ghi name và price vào drop_log.txt
    drop_items = scan_drop_log(changed_text, id_table=id_table, price_table=price_table)
    if not drop_items:
        return
    
    # Xử lý từng drop item
    for item in drop_items:
        item_id = item.get("itemId")
        num = item.get("num", 0)  # Số lượng hiện tại trong túi (từ BagMgr sau khi nhặt)
        
        if not item_id:
            continue
        
        item_id_str = str(item_id)
        item_id_int = int(item_id)
        
        # Tính số lượng mới nhặt được: so sánh với số lượng trước đó (từ init bag hoặc lần trước)
        previous_quantity = previous_item_quantities.get(item_id_int, 0)
        current_quantity = num  # Số lượng hiện tại trong túi sau khi nhặt
        
        # Số lượng mới nhặt = số lượng hiện tại - số lượng trước đó
        new_quantity = current_quantity - previous_quantity
        
        if new_quantity <= 0:
            # Không có item mới nhặt, chỉ là update số lượng
            # Vẫn cập nhật previous_quantity để track
            previous_item_quantities[item_id_int] = current_quantity
            continue
        
        # Log khi nhặt được item
        log_debug(f"drop item {item_id_str} x{new_quantity}")
        
        # Lấy name từ id_table
        item_name = id_table.get(item_id_str, f"Item {item_id_str}")
        
        # Check if in exclude list
        if exclude_list and item_name in exclude_list:
            continue
        
        # Cập nhật previous_quantity để track cho lần sau
        previous_item_quantities[item_id_int] = current_quantity
        
        # Cập nhật drop_list
        if item_id_int not in drop_list:
            drop_list[item_id_int] = 0
        drop_list[item_id_int] += new_quantity
        
        if item_id_int not in drop_list_all:
            drop_list_all[item_id_int] = 0
        drop_list_all[item_id_int] += new_quantity
        
        # Tính giá
        price = 0.0
        if item_id_str in price_table:
            price = price_table[item_id_str]
            if config_data.get("tax", 0) == 1 and item_id_str != "100300":
                price = price * 0.875
            income += price * new_quantity
            income_all += price * new_quantity
        
        # Ghi vào log/drop.txt
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] Drop: {item_name} x{new_quantity} ({round(price, 3)}/each)\n"
        drop_log_path = os.path.join("log", "drop.txt")
        os.makedirs("log", exist_ok=True)
        with open(drop_log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    
    if drop_items:
        # Schedule reshow() từ main thread để tránh blocking và lỗi Tkinter
        try:
            if state.root and state.root.winfo_exists():
                state.root.after(0, state.root.reshow)
        except (RuntimeError, AttributeError):
            # Main loop đã kết thúc, bỏ qua
            pass
        
        if state.is_in_map == False:
            state.is_in_map = True

