"""
Price Handler Module
====================

Mục đích:
    Module này xử lý tất cả logic liên quan đến giá của items:
    - Tự động lấy giá từ exchange khi người chơi tra giá trong game
    - Đồng bộ giá từ server
    - Gửi giá mới lên server để chia sẻ với cộng đồng

Tác dụng:
    - Monitor log để phát hiện khi người chơi tra giá trong exchange
    - Extract giá từ exchange search results
    - Cập nhật full_table.json với giá mới
    - Đồng bộ giá từ server mỗi 90 giây
    - Xử lý pending items (items chưa có trong local database)

Các function chính:
    - get_price_info(): Extract và update giá từ exchange log
    - price_update(): Background thread cập nhật giá từ server
    - price_submit(): Gửi giá lên server
    - get_user(): Lấy hoặc đăng ký user ID
"""
import time
import json
import re
import requests as rq

server = "serverp.furtorch.heili.tech"


def get_price_info(text):
    """Extract and update price information from exchange search results"""
    try:
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
            else:
                num_values = min(len(values), 30)
                sum_values = sum(float(values[i]) for i in range(num_values))
                average_value = sum_values / num_values
            with open("full_table.json", 'r', encoding="utf-8") as f:
                full_table = json.load(f)
                try:
                    full_table[ids]['last_time'] = round(time.time())
                    #full_table[ids]['from'] = "Local"
                    full_table[ids]['from'] = "FurryHeiLi"
                    full_table[ids]['price'] = round(average_value, 4)
                except:
                    pass
            with open("full_table.json", 'w', encoding="utf-8") as f:
                json.dump(full_table, f, indent=4, ensure_ascii=False)
            print(f'Updated item value: ID:{ids}, Name:{full_table[ids]["name"]}, Price:{round(average_value, 4)}')
            price_submit(ids, round(average_value, 4), get_user())
    except Exception as e:
        print(e)


def price_update(pending_items_getter):
    """
    Update prices from server
    
    Args:
        pending_items_getter: Function to get pending items dict
    """
    while True:
        try:
            r = rq.get(f"http://{server}/get", timeout=10).json()
            with open("full_table.json", 'w', encoding="utf-8") as f:
                json.dump(r, f, indent=4, ensure_ascii=False)
            print("Price update successful")
            n = pending_items_getter()
            for i in list(n.keys()):  # Use list to avoid dict size change during iteration
                r = rq.get(f"http://{server}/gowork?id="+i, timeout=10).json()
                del n[i]
                print(f"[Network] ID {i} fetch completed")
            time.sleep(90)
        except Exception as e:
            print("Price update failed: " + str(e))
            time.sleep(10)


def price_submit(ids, price, user):
    """Submit price update to server"""
    print(price)
    try:
        r = rq.get(f"http://{server}/update?user={user}&ids={ids}&new_price={price}", timeout=10).json()
        print(r)
        return r
    except Exception as e:
        print(e)


def get_user():
    """Get or register user ID"""
    with open("config.json", "r", encoding="utf-8") as f:
        config_data = json.load(f)
    if not config_data.get("user", False):
        try:
            r = rq.get(f"http://{server}/reg", timeout=10).json()
            config_data["user"] = r["user_id"]
            user_id = r["user_id"]
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except:
            user_id = "3b95f1d6-5357-4efb-a96b-8cc3c76b3ee0"
    else:
        user_id = config_data["user"]
    return user_id

