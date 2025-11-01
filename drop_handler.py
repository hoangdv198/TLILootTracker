"""
Drop Handler Module
===================

Mục đích:
    Module này xử lý tất cả logic liên quan đến drop items từ game:
    - Phát hiện khi vào/ra map
    - Xử lý và thống kê các items rơi ra
    - Tính toán giá trị và ghi vào file drop.txt

Tác dụng:
    - Theo dõi trạng thái vào/ra map
    - Parse và xử lý drop items từ log
    - Cập nhật statistics (drop_list, income, etc.)
    - Ghi log drops vào file drop.txt để theo dõi

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
from datetime import datetime
from log_parser import convert_from_log_structure, scanned_log


# Global state variables (will be initialized in main)
pending_items = {}
exclude_list = []
drop_list = {}
drop_list_all = {}
income = 0
income_all = 0
config_data = {}


def deal_drop(drop_data, item_id_table, price_table):
    """Update drop statistics"""
    global income, income_all, drop_list, drop_list_all, config_data, pending_items, exclude_list
    
    def invoke_drop_item_processing(item_data, item_key):
        global income, income_all, drop_list, drop_list_all, exclude_list, pending_items, config_data
        """Process single dropped item data"""
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
        item_name = base_id_str  # Default to using ID as name

        if base_id_str in item_id_table:
            item_name = item_id_table[base_id_str]
        else:
            # No local data, add to pending queue
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

        # Check if in exclude list
        global exclude_list
        if exclude_list and item_name in exclude_list:
            print(f"Excluded: {item_name} x{num}")
            return
        print(base_id)
        # Count quantity
        if base_id not in drop_list:
            drop_list[base_id] = 0
        drop_list[base_id] += num

        if base_id not in drop_list_all:
            drop_list_all[base_id] = 0
        drop_list_all[base_id] += num

        # Calculate price
        price = 0.0
        if str(base_id) in price_table:
            base_id = str(base_id)
            price = price_table[base_id]
            if config_data.get("tax", 0) == 1 and base_id != "100300":
                price = price * 0.875
            income += price * num
            income_all += price * num

        # Record to file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] Drop: {item_name} x{num} ({round(price, 3)}/each)\n"
        with open("drop.txt", "a", encoding="utf-8") as f:
            f.write(log_line)

    def invoke_drop_items_recursive(data, path=""):
        """Recursively process all dropped items"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            # Check if contains drop data
            if isinstance(value, dict) and "item" in value:
                # Check if has Picked marker
                has_picked = ("Picked" in value) or \
                             (isinstance(value["item"], dict) and "Picked" in value["item"])

                if has_picked:
                    invoke_drop_item_processing(value, current_path)

            # Recursively process child items
            if isinstance(value, dict):
                invoke_drop_items_recursive(value, current_path)

    # Start recursive processing
    invoke_drop_items_recursive(drop_data)


def deal_change(changed_text):
    """
    Process log changes: detect map entry/exit and handle drops
    
    Note: This function uses global variables that must be defined in the main module
    """
    import index as main_module
    global drop_list, income, drop_list_all, income_all, config_data
    
    # Detect map entry
    if "PageApplyBase@ _UpdateGameEnd: LastSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200/XZ_YuJinZhiXiBiNanSuo200.XZ_YuJinZhiXiBiNanSuo200' NextSceneName = World'/Game/Art/Maps" in changed_text:
        main_module.is_in_map = True
        drop_list = {}
        income = -main_module.root.cost
        income_all += -main_module.root.cost
        main_module.map_count += 1
        
    # Detect map exit
    if "NextSceneName = World'/Game/Art/Maps/01SD/XZ_YuJinZhiXiBiNanSuo200/XZ_YuJinZhiXiBiNanSuo200.XZ_YuJinZhiXiBiNanSuo200'" in changed_text:
        main_module.is_in_map = False
        main_module.total_time += time.time() - main_module.t
    
    # Load item ID and price tables
    texts = changed_text
    id_table = {}
    price_table = {}
    with open("full_table.json", 'r', encoding="utf-8") as f:
        f = json.load(f)
    for i in f.keys():
        id_table[str(i)] = f[i]["name"]
        price_table[str(i)] = f[i]["price"]
    
    # Find and process drops
    texts = scanned_log(texts)
    if texts == []:
        return
    
    for text in texts:
        text = convert_from_log_structure(text)
        deal_drop(text, id_table, price_table)
    
    print(texts)
    if texts != []:
        main_module.root.reshow()
        if main_module.is_in_map == False:
            main_module.is_in_map = True

