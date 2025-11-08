"""
Price Service
=============

Service này chứa business logic liên quan đến price handling:
- Extract và parse giá từ exchange log
- Đồng bộ giá từ server
- Quản lý user ID
- Xử lý pending items

Service này sử dụng repositories để giao tiếp với external APIs.
"""
import time
import json
import re
from repositories.price_api_client import (
    fetch_all_prices,
    fetch_item_by_id,
    submit_price,
    register_user
)


def get_user():
    """
    Lấy hoặc đăng ký user ID từ config.json
    
    Business logic: Kiểm tra config, đăng ký nếu chưa có, lưu vào config
    
    Returns:
        str: User ID
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        if not config_data.get("user", False):
            try:
                r = register_user()
                config_data["user"] = r["user_id"]
                user_id = r["user_id"]
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
            except:
                # Fallback user ID nếu không thể đăng ký
                user_id = "3b95f1d6-5357-4efb-a96b-8cc3c76b3ee0"
        else:
            user_id = config_data["user"]
        
        return user_id
    except Exception as e:
        print(f"Error getting user: {e}")
        # Fallback user ID
        return "3b95f1d6-5357-4efb-a96b-8cc3c76b3ee0"


def get_price_info(text):
    """
    Extract và update giá từ exchange search results trong log
    
    Business logic:
    - Parse log để tìm price information
    - Tính toán average price từ exchange data
    - Ghi log vào search_price_log.json (giá đắt nhất)
    - Submit price lên server
    
    Args:
        text (str): Log text từ game
    """
    try:
        # Load id_table.json một lần để tối ưu performance
        try:
            with open("id_table.json", 'r', encoding="utf-8") as f:
                id_table = json.load(f)
        except Exception as e:
            print(f'Error reading id_table.json: {e}')
            id_table = {}
        
        pattern_id = r'XchgSearchPrice----SynId = (\d+).*?\+refer \[(\d+)\]'
        match = re.findall(pattern_id, text, re.DOTALL)
        result = list(match)
        for i, item in enumerate(result, 1):
            ids = item[1]
            synid = item[0]
            pattern = re.compile(
                rf'----Socket RecvMessage STT----XchgSearchPrice----SynId = {synid}\s+'  # Match target SynId
                r'\[.*?\]\s*GameLog: Display: \[Game\]\s+'  # Match time and fixed prefix
                r'(.*?)(?=----Socket RecvMessage STT----|$)',  # Match data block content (to next block or end)
                re.DOTALL  # Allow . to match newlines
            )

            # Find target data block
            match = pattern.search(text)
            data_block = match.group(1)
            if not match:
                print(f'Found record: ID:{item[1]}, Price:-1')
            if int(item[1]) == 100300:
                continue
            # Extract all numeric values from +number [value] (ignore currency)
            value_pattern = re.compile(r'\+\d+\s+\[([\d.]+)\]')  # Match +number [x.x] format
            values = value_pattern.findall(data_block)
            # Get average of first 30 values, but if values length is less than 30, take average of all
            if len(values) == 0:
                average_value = -1
                highest_price = -1
            else:
                num_values = min(len(values), 30)
                sum_values = sum(float(values[i]) for i in range(num_values))
                average_value = sum_values / num_values
                # Lấy giá cuối cùng (giá đắt nhất) - giá cuối cùng trong list
                highest_price = float(values[-1])
            
            # Lấy type và name từ id_table.json (đã dịch sang tiếng Anh)
            item_type = id_table.get(ids, {}).get('type', 'Unknown')
            item_name = id_table.get(ids, {}).get('name', f'Item {ids}')
            
            print(f'Updated item value: ID:{ids}, Name:{item_name}, Price:{round(average_value, 4)}')
            
            # Ghi vào search_price_log.json
            if highest_price > 0:
                try:
                    # Đọc file log hiện tại hoặc tạo mới
                    try:
                        with open("search_price_log.json", 'r', encoding="utf-8") as f:
                            price_log = json.load(f)
                    except FileNotFoundError:
                        price_log = []
                    
                    # Tạo entry mới
                    log_entry = {
                        "idItem": ids,
                        "price": round(highest_price, 4),
                        "last_update": round(time.time()),
                        "type": item_type
                    }
                    
                    # Tìm xem đã có entry với idItem này chưa
                    found = False
                    for idx, entry in enumerate(price_log):
                        if entry.get("idItem") == ids:
                            price_log[idx] = log_entry  # Update entry cũ
                            found = True
                            break
                    
                    if not found:
                        price_log.append(log_entry)  # Thêm entry mới
                    
                    # Ghi lại file
                    with open("search_price_log.json", 'w', encoding="utf-8") as f:
                        json.dump(price_log, f, indent=4, ensure_ascii=False)
                    
                    print(f'Logged to search_price_log.json: ID:{ids}, Price:{round(highest_price, 4)}, Type:{item_type}')
                except Exception as e:
                    print(f'Error writing to search_price_log.json: {e}')
            
            # TODO: Re-enable submit price to server
            # submit_price(ids, round(average_value, 4), get_user())
    except Exception as e:
        print(e)


def price_update(pending_items_getter):
    """
    Background thread để đồng bộ giá từ server
    
    Business logic:
    - Fetch tất cả prices từ server mỗi 90 giây
    - Lưu vào search_price_log.json
    - Xử lý pending items (items chưa có trong local)
    
    Args:
        pending_items_getter: Function để lấy pending items dict
    
    TODO: Re-enable sync từ server sau khi hoàn thiện
    """
    # TODO: Re-enable sync từ server
    # Tính năng sync từ server đã được tạm thời disable
    print("[INFO] Price sync from server is currently disabled")
    while True:
        try:
            # TODO: Re-enable sync logic
            # r = fetch_all_prices()
            # # Convert server data to search_price_log.json format
            # price_log = []
            # for item_id, item_data in r.items():
            #     price_log.append({
            #         "idItem": item_id,
            #         "price": item_data.get("price", 0),
            #         "last_update": item_data.get("last_update", round(time.time())),
            #         "type": item_data.get("type", "Unknown")
            #     })
            # with open("search_price_log.json", 'w', encoding="utf-8") as f:
            #     json.dump(price_log, f, indent=4, ensure_ascii=False)
            # print("Price update successful")
            # n = pending_items_getter()
            # for i in list(n.keys()):  # Use list to avoid dict size change during iteration
            #     r = fetch_item_by_id(i)
            #     del n[i]
            #     print(f"[Network] ID {i} fetch completed")
            time.sleep(90)
        except Exception as e:
            print("Price update failed: " + str(e))
            time.sleep(10)

