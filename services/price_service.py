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
from core.logger import log_debug
from repositories.price_api_client import (
    fetch_all_prices,
    fetch_item_by_id,
    submit_price,
    register_user
)
from .log_scan_service import scan_price_search
from .item_service import get_item_info


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
    - Sử dụng scan_price_search() để scan và extract giá từ log
    - Tính toán average price từ exchange data
    - Ghi log vào search_price_log.json (giá cao nhất - max value)
    - Submit price lên server
    
    Args:
        text (str): Log text từ game
    """
    try:
        
        # Sử dụng scan_price_search để scan và extract giá
        price_results = scan_price_search(text)
        
        for result in price_results:
            item_id = result.get("itemId")
            highest_price = result.get("highest_price", -1)
            average_price = result.get("average_price", -1)
            
            if average_price <= 0:
                continue
            
            # Lấy type và name từ item_service
            item_info = get_item_info(item_id, apply_tax=False)
            item_type = item_info.get("type", "Unknown")
            item_name = item_info.get("name", f"Item {item_id}")
            
            # Print thông tin: average (giá được lưu) và highest (để tham khảo)
            log_debug(f'Updated item value: ID:{item_id}, Name:{item_name}, Average Price:{average_price}, Highest Price:{highest_price}')
            
            # Ghi vào search_price_log.json (lưu average_price - giá trung bình của tất cả giá trị)
            try:
                # Đọc file log hiện tại hoặc tạo mới
                try:
                    with open("search_price_log.json", 'r', encoding="utf-8") as f:
                        price_log = json.load(f)
                except FileNotFoundError:
                    price_log = []
                
                # Tạo entry mới
                # Làm tròn price về 4 chữ số thập phân (ví dụ: 0.001)
                rounded_price = round(average_price, 4) if average_price > 0 else 0.0
                log_entry = {
                    "idItem": item_id,
                    "name": item_name,
                    "price": rounded_price,
                    "last_update": round(time.time()),
                    "type": item_type
                }
                
                # Tìm xem đã có entry với idItem này chưa
                found = False
                for idx, entry in enumerate(price_log):
                    if entry.get("idItem") == item_id:
                        price_log[idx] = log_entry  # Update entry cũ
                        found = True
                        break
                
                if not found:
                    price_log.append(log_entry)  # Thêm entry mới
                
                # Ghi lại file
                with open("search_price_log.json", 'w', encoding="utf-8") as f:
                    json.dump(price_log, f, indent=4, ensure_ascii=False)
                
                log_debug(f'Logged to search_price_log.json: ID:{item_id}, Price:{average_price}, Type:{item_type}')
            except Exception as e:
                print(f'Error writing to search_price_log.json: {e}')
            
            # TODO: Re-enable submit price to server
            # submit_price(item_id, average_price, get_user())
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

