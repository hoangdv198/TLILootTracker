"""
Log Scan Service Module
=======================

Mục đích:
    Module này cung cấp các service functions để scan log theo từng lĩnh vực:
    - scan_init_bag: Scan init bag data (BagMgr@:InitBagData)
    - scan_drop_log: Scan drops từ log (PickItems format)
    - scan_price_search: Scan price search results từ log
    - Có thể mở rộng thêm các scan functions khác

Tác dụng:
    - Tách biệt logic scan theo từng domain
    - Dễ dàng maintain và extend
    - Cung cấp interface rõ ràng cho các module khác sử dụng
"""
import re
import os
import json
from typing import List, Dict, Optional
from core.logger import log_debug
from .item_service import get_item_info
from app import state
from datetime import datetime


def init_bag_data():
    """
    Load bag_items từ bag_log.json khi start app để có cache trước đó
    
    Returns:
        bool: True nếu load thành công, False nếu không
    """
    try:
        bag_log_path = os.path.join("log", "bag_log.json")
        if os.path.exists(bag_log_path):
            with open(bag_log_path, 'r', encoding="utf-8") as f:
                bag_log_data = json.load(f)
                if isinstance(bag_log_data, dict) and "items" in bag_log_data:
                    state.bag_items = bag_log_data["items"]
                    log_debug(f"init_bag_data: Loaded {len(state.bag_items)} items from bag_log.json")
                    return True
                elif isinstance(bag_log_data, list) and len(bag_log_data) > 0:
                    # Nếu là list, lấy entry cuối cùng
                    latest_entry = bag_log_data[-1]
                    if isinstance(latest_entry, dict) and "items" in latest_entry:
                        state.bag_items = latest_entry["items"]
                        log_debug(f"init_bag_data: Loaded {len(state.bag_items)} items from bag_log.json (latest entry)")
                        return True
        return False
    except Exception as e:
        log_debug(f"init_bag_data: Error loading bag_log.json: {e}")
        return False


def scan_init_bag(changed_text: str) -> Dict[str, Dict]:
    """
    Scan init bag data từ log theo format BagMgr@:InitBagData
    
    Format log:
        "BagMgr@:InitBagData PageId = ... SlotId = ... ConfigBaseId = ... Num = ..."
    
    Args:
        changed_text (str): Nội dung log mới được đọc từ file
    
    Returns:
        Dict[str, Dict]: Dictionary với key là itemId, value là dict chứa thông tin:
        {
            "itemId": {
                "pageId": 102,
                "slotId": 0,
                "num": 123,
                "timestamp": "2025.11.08-18.24.00:451"
            },
            ...
        }
        
    Note: Nếu cùng itemId xuất hiện nhiều lần, sẽ lấy entry cuối cùng (số lượng mới nhất)
    """
    bag_data = {}
    lines = changed_text.split('\n')
    
    # Ghi log init bag events vào file để debug
    init_bag_log_path = os.path.join("log", "init_bag_msg.log")
    init_bag_lines = []
    
    for line in lines:
        # Tìm pattern: "BagMgr@:InitBagData PageId = ... SlotId = ... ConfigBaseId = ... Num = ..."
        if 'BagMgr@:InitBagData' in line and 'ConfigBaseId' in line:
            # Ghi log line vào file để debug
            init_bag_lines.append(line)
            # Extract timestamp
            timestamp_match = re.search(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\]', line)
            timestamp = timestamp_match.group(1) if timestamp_match else ""
            
            # Extract PageId, SlotId, ConfigBaseId, Num
            page_id_match = re.search(r'PageId\s*=\s*(\d+)', line)
            slot_id_match = re.search(r'SlotId\s*=\s*(\d+)', line)
            config_base_id_match = re.search(r'ConfigBaseId\s*=\s*(\d+)', line)
            num_match = re.search(r'Num\s*=\s*(\d+)', line)
            
            if config_base_id_match:
                item_id = config_base_id_match.group(1)
                bag_data[item_id] = {
                    "pageId": int(page_id_match.group(1)) if page_id_match else 0,
                    "slotId": int(slot_id_match.group(1)) if slot_id_match else 0,
                    "num": int(num_match.group(1)) if num_match else 0,
                    "timestamp": timestamp
                }
    
    # Ghi tất cả init bag log lines vào file
    if init_bag_lines:
        try:
            os.makedirs("log", exist_ok=True)
            with open(init_bag_log_path, 'a', encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n========== Init Bag Event - {timestamp} ==========\n")
                for log_line in init_bag_lines:
                    f.write(log_line + "\n")
                f.write(f"========== End Init Bag Event ({len(init_bag_lines)} lines) ==========\n\n")
            log_debug(f"scan_init_bag: wrote {len(init_bag_lines)} init bag log lines to init_bag_msg.log")
        except Exception as e:
            log_debug(f"scan_init_bag: error writing to init_bag_msg.log: {e}")
    
    if bag_data:
        log_debug(f"scan_init_bag: found {len(bag_data)} items in bag")
        
        # Tự động update vào state.bag_items khi scan được data
        try:
            # Load id_table để lấy tên items
            id_table = {}
            try:
                with open("id_table.json", 'r', encoding="utf-8") as f:
                    id_table_data = json.load(f)
                for item_id, item_data in id_table_data.items():
                    id_table[str(item_id)] = item_data.get("name", f"Item {item_id}")
            except Exception as e:
                log_debug(f"error reading id_table.json in scan_init_bag: {e}")
            
            # Update state.bag_items với format đầy đủ
            state.bag_items = {}
            for item_id_str, bag_info in bag_data.items():
                item_name = id_table.get(item_id_str, f"Item {item_id_str}")
                state.bag_items[item_id_str] = {
                    "name": item_name,
                    "pageId": bag_info.get("pageId", 0),
                    "slotId": bag_info.get("slotId", 0),
                    "num": bag_info.get("num", 0)
                }
            log_debug(f"scan_init_bag: updated state.bag_items with {len(state.bag_items)} items")
        except Exception as e:
            log_debug(f"error updating state.bag_items in scan_init_bag: {e}")
    
    return bag_data


def scan_drop_log(changed_text: str, id_table: dict = None, price_table: dict = None) -> List[Dict]:
    """
    Scan drop items từ log theo format PickItems
    
    Format log:
        - Start: "ItemChange@ ProtoName=PickItems start"
        - Update: "ItemChange@ Update Id=... BagNum=... in PageId=... SlotId=..."
        - BagMgr: "BagMgr@:Modfy BagItem PageId = ... SlotId = ... ConfigBaseId = ... Num = ..."
        - End: "ItemChange@ ProtoName=PickItems end"
    
    Args:
        changed_text (str): Nội dung log mới được đọc từ file
        id_table (dict, optional): DEPRECATED - Sử dụng item_service.get_item_info() thay thế
        price_table (dict, optional): DEPRECATED - Sử dụng item_service.get_item_info() thay thế
    
    Returns:
        List[Dict]: List các drop items với format:
        [
            {
                "itemId": "100300",
                "num": 96,
                "bagNum": 96,
                "slotId": 0,
                "pageId": 102,
                "timestamp": "2025.11.08-16.59.48:014"
            },
            ...
        ]
    
    Note:
        - id_table và price_table parameters được giữ lại để backward compatibility
        - Logic lookup name và price đã được chuyển sang sử dụng item_service.get_item_info()
    """
    drop_items = []
    lines = changed_text.split('\n')
    line_count = len(lines)
    
    i = 0
    while i < line_count:
        line = lines[i]
        
        # Tìm start marker: "ItemChange@ ProtoName=PickItems start"
        if 'ItemChange@ ProtoName=PickItems start' in line:
            current_item = {}
            # Extract timestamp từ start line: [2025.11.08-16.59.48:014]
            timestamp_match = re.search(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\]', line)
            if timestamp_match:
                current_item["timestamp"] = timestamp_match.group(1)
            
            j = i + 1
            
            # Scan các dòng trong block cho đến khi gặp end
            while j < line_count:
                current_line = lines[j]
                
                # End marker: "ItemChange@ ProtoName=PickItems end"
                if 'ItemChange@ ProtoName=PickItems end' in current_line:
                    # Nếu đã có đủ thông tin, thêm vào list và ghi log
                    if current_item.get("itemId"):
                        drop_items.append(current_item)
                        
                        # Ghi vào log/drop_log.txt
                        try:
                            # Tạo folder log nếu chưa có
                            log_dir = "log"
                            if not os.path.exists(log_dir):
                                os.makedirs(log_dir)
                            
                            # Lấy các thông tin từ current_item
                            timestamp = current_item.get("timestamp", "")
                            page_id = current_item.get("pageId", 0)
                            slot_id = current_item.get("slotId", 0)
                            config_base_id = current_item.get("itemId", "")
                            num = current_item.get("num", 0)
                            
                            # Lấy name và price từ item_service
                            item_info = get_item_info(config_base_id, apply_tax=False)
                            item_name = item_info.get("name", f"Item {config_base_id}")
                            item_price = item_info.get("price", 0.0)
                            
                            # Format: [2025.11.08-16.59.48:014][PickItems] BagItem PageId = 102 SlotId = 0 ConfigBaseId = 100300 Num = 101 Name = Memory Fragments Price = 0.0
                            if timestamp:
                                log_line = f"[{timestamp}][PickItems] BagItem PageId = {page_id} SlotId = {slot_id} ConfigBaseId = {config_base_id} Num = {num} Name = {item_name} Price = {round(item_price, 4)}\n"
                                
                                drop_log_path = os.path.join(log_dir, "drop_log.txt")
                                with open(drop_log_path, "a", encoding="utf-8") as f:
                                    f.write(log_line)
                        except Exception as e:
                            log_debug(f"error writing to drop_log.txt: {e}")
                    break
                
                # Parse Update line: "ItemChange@ Update Id=... BagNum=... in PageId=... SlotId=..."
                if 'ItemChange@ Update' in current_line and 'BagNum=' in current_line:
                    # Extract BagNum, PageId, SlotId
                    bag_num_match = re.search(r'BagNum=(\d+)', current_line)
                    page_id_match = re.search(r'PageId=(\d+)', current_line)
                    slot_id_match = re.search(r'SlotId=(\d+)', current_line)
                    
                    if bag_num_match:
                        current_item["bagNum"] = int(bag_num_match.group(1))
                    if page_id_match:
                        current_item["pageId"] = int(page_id_match.group(1))
                    if slot_id_match:
                        current_item["slotId"] = int(slot_id_match.group(1))
                
                # Parse BagMgr line: "BagMgr@:Modfy BagItem PageId = ... SlotId = ... ConfigBaseId = ... Num = ..."
                if 'BagMgr@:Modfy BagItem' in current_line and 'ConfigBaseId' in current_line:
                    # Extract ConfigBaseId và Num
                    config_base_id_match = re.search(r'ConfigBaseId\s*=\s*(\d+)', current_line)
                    num_match = re.search(r'Num\s*=\s*(\d+)', current_line)
                    
                    if config_base_id_match:
                        current_item["itemId"] = config_base_id_match.group(1)
                    if num_match:
                        current_item["num"] = int(num_match.group(1))
                    
                    # Nếu chưa có timestamp, lấy từ BagMgr line
                    if not current_item.get("timestamp"):
                        timestamp_match = re.search(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\]', current_line)
                        if timestamp_match:
                            current_item["timestamp"] = timestamp_match.group(1)
                
                j += 1
            
            # Move to next line after block
            i = j + 1
        else:
            i += 1
    
    if drop_items:
        log_debug(f"scan_drop_log: found {len(drop_items)} drop item(s)")
    return drop_items


def scan_price_search(changed_text: str) -> List[Dict]:
    """
    Scan price search results từ log và extract giá từ unitPrices block
    
    Format log:
        - Pattern: "XchgSearchPrice----SynId = ... +refer [...]"
        - Extract SynId và ItemId từ pattern
        - Extract giá từ unitPrices block (từ +1 đến +100)
    
    Args:
        changed_text (str): Nội dung log mới được đọc từ file
    
    Returns:
        List[Dict]: List các price search results với format:
        [
            {
                "synId": "12345",
                "itemId": "360404",
                "values": ["0.17017", "0.17125", ...],  # List giá từ unitPrices
                "average_price": 0.1752,  # Average của 30 giá trị đầu
                "highest_price": 0.18018  # Giá cao nhất (max value) từ tất cả giá trị
            },
            ...
        ]
    """
    results = []
    
    # Pattern: XchgSearchPrice----SynId = (\d+).*?\+refer \[(\d+)\]
    pattern_id = r'XchgSearchPrice----SynId\s*=\s*(\d+).*?\+refer\s*\[(\d+)\]'
    matches = re.findall(pattern_id, changed_text, re.DOTALL)
    
    for syn_id, item_id in matches:
        # Tìm data block cho synId này
        data_block_pattern = re.compile(
            rf'----Socket RecvMessage STT----XchgSearchPrice----SynId = {syn_id}\s+'  # Match target SynId
            r'\[.*?\]\s*GameLog: Display: \[Game\]\s+'  # Match time and fixed prefix
            r'(.*?)(?=----Socket RecvMessage STT----|$)',  # Match data block content (to next block or end)
            re.DOTALL  # Allow . to match newlines
        )
        
        data_block_match = data_block_pattern.search(changed_text)
        if not data_block_match:
            continue
        
        data_block = data_block_match.group(1)
        
        # Skip currency 100300
        if int(item_id) == 100300:
            continue
        
        # Extract chỉ các giá trị từ unitPrices block (từ +1 đến +100)
        # Logic regex 2 tầng (tối ưu):
        # Bước 1: Tách block unitPrices từ "unitPrices+1 [value]" đến trước dòng "+currency"
        # Bước 2: Scan tất cả các giá trị trong block đó
        
        values = []
        
        # Bước 1: Tìm block unitPrices
        # Pattern: unitPrices+1 [value] ... (dừng khi gặp +currency hoặc hết chuỗi)
        # Format log có thể là:
        #   +prices+1+unitPrices+1 [value]
        #   hoặc
        #   unitPrices+1 [value]
        # Sử dụng pattern theo user suggestion: regex 2 tầng tối ưu
        # Pattern match cả 2 format: +prices+1+unitPrices+1 hoặc unitPrices+1
        block_pattern = re.compile(
            r'(?:\+prices\+1\+)?unitPrices\+1\s*\[([^\]]+)\]\s*\n([\s\S]*?)(?=^\s*\|.*?\+currency|\Z)',
            re.MULTILINE
        )
        
        block_match = block_pattern.search(data_block)
        if block_match:
            # Lấy giá trị đầu tiên từ dòng unitPrices+1
            first_value = block_match.group(1)
            values.append(first_value)
            
            # Lấy phần còn lại của block (từ dòng +2 trở đi)
            unit_prices_block = block_match.group(2)
            
            # Bước 2: Scan các giá trị trong block
            # Pattern: |      | |          +number [value] (có prefix | và spaces)
            # Match cả dòng có format: |      | |          +2 [value]
            # Pattern này match các dòng có format: |      | |          +number [value]
            # với bất kỳ số lượng | và spaces nào trước +number
            value_pattern = re.compile(
                r'^\s*(?:\|[^\n]*)*\+(\d+)\s*\[(-?\d+(?:\.\d+)?)\]\s*$',
                re.MULTILINE
            )
            
            # Lấy tất cả các cặp (index, value) từ block
            value_matches = value_pattern.findall(unit_prices_block)
            
            # Debug: log số lượng matches
            if len(value_matches) == 0:
                log_debug(f"scan_price_search: WARNING - No value matches found in block for itemId={item_id}, block_length={len(unit_prices_block)}")
            
            # Lọc chỉ lấy từ +2 đến +100
            for index_str, value_str in value_matches:
                index = int(index_str)
                if 2 <= index <= 100:
                    values.append(value_str)
                elif index > 100:
                    # Dừng khi gặp số > 100
                    break
        else:
            # Debug: log khi không tìm thấy block
            log_debug(f"scan_price_search: WARNING - No unitPrices block found for itemId={item_id}, synId={syn_id}")
        
        # Tính average và highest price
        average_price = -1
        highest_price = -1
        
        if len(values) > 0:
            # Tính trung bình của TẤT CẢ các giá trị trong array (không giới hạn 30)
            # Công thức: tổng tất cả giá trị / số lượng giá trị
            num_values = len(values)
            sum_values = sum(float(v) for v in values)
            average_price = sum_values / num_values
            # Lấy giá cao nhất (max value) từ tất cả các giá trị trong list
            highest_price = max(float(v) for v in values)
            
            # Log để debug: hiển thị số lượng và list values scan được
            values_float = [float(v) for v in values]
            log_debug(f"scan_price_search: itemId={item_id}, synId={syn_id}, values_count={len(values)}, prices={values_float}")
            log_debug(f"scan_price_search: itemId={item_id}, average_price={round(average_price, 4)}, highest_price={round(highest_price, 4)}")
        
        results.append({
            "synId": syn_id,
            "itemId": item_id,
            "values": values,
            "average_price": round(average_price, 4) if average_price > 0 else -1,
            "highest_price": round(highest_price, 4) if highest_price > 0 else -1
        })
    
    if results:
        log_debug(f"scan_price_search: found {len(results)} result(s)")
    return results

