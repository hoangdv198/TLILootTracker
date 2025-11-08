"""
Test script cho scan_price_search function

Mục đích:
    Test function scan_price_search() với data sample từ UE_game.log
    để kiểm tra xem logic scan có hoạt động đúng không

Cách chạy:
    python test_scan_price_search.py
"""
import os
import re
from typing import List, Dict


# Mock logger
def log_debug(message):
    """Mock logger function"""
    print(f"[DEBUG] {message}")


# Copy function scan_price_search từ log_scan_service.py để test độc lập
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
            value_pattern = re.compile(
                r'^\s*(?:\|[^\n]*)*\+(\d+)\s*\[(-?\d+(?:\.\d+)?)\]\s*$',
                re.MULTILINE
            )
            
            # Lấy tất cả các cặp (index, value) từ block
            value_matches = value_pattern.findall(unit_prices_block)
            
            # Lọc chỉ lấy từ +2 đến +100
            for index_str, value_str in value_matches:
                index = int(index_str)
                if 2 <= index <= 100:
                    values.append(value_str)
                elif index > 100:
                    # Dừng khi gặp số > 100
                    break
        
        # Tính average và highest price
        average_price = -1
        highest_price = -1

        if len(values) > 0:
            num_values = min(len(values), 30)
            sum_values = sum(float(values[i]) for i in range(num_values))
            average_price = sum_values / num_values
            # Lấy giá cao nhất (max value) từ tất cả các giá trị trong list
            highest_price = max(float(v) for v in values)
        
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


def test_scan_price_search_from_file(log_file_path: str, start_line: int = None, end_line: int = None):
    """
    Test scan_price_search với data từ file log
    
    Args:
        log_file_path (str): Đường dẫn đến file log
        start_line (int, optional): Dòng bắt đầu để đọc (để test với sample nhỏ)
        end_line (int, optional): Dòng kết thúc để đọc
    """
    print("=" * 80)
    print("TEST: scan_price_search")
    print("=" * 80)
    
    # Đọc file log
    try:
        with open(log_file_path, 'r', encoding="utf-8") as f:
            if start_line and end_line:
                # Đọc chỉ một phần của file (sample)
                lines = f.readlines()
                sample_lines = lines[start_line-1:end_line]
                log_text = ''.join(sample_lines)
                print(f"Reading lines {start_line} to {end_line} from {log_file_path}")
            else:
                # Đọc toàn bộ file (có thể rất lớn)
                log_text = f.read()
                print(f"Reading entire file: {log_file_path}")
    except FileNotFoundError:
        print(f"ERROR: File not found: {log_file_path}")
        return
    except Exception as e:
        print(f"ERROR: Failed to read file: {e}")
        return
    
    print(f"Log text length: {len(log_text)} characters")
    print("-" * 80)
    
    # Test scan_price_search
    print("\nCalling scan_price_search()...")
    results = scan_price_search(log_text)
    
    # Hiển thị kết quả
    print(f"\nFound {len(results)} price search result(s)")
    print("=" * 80)
    
    for idx, result in enumerate(results, 1):
        print(f"\nResult #{idx}:")
        print(f"  synId: {result.get('synId')}")
        print(f"  itemId: {result.get('itemId')}")
        print(f"  values_count: {len(result.get('values', []))}")
        print(f"  average_price: {result.get('average_price')}")
        print(f"  highest_price: {result.get('highest_price')}")
        
        # Hiển thị list prices
        values = result.get('values', [])
        if values:
            values_float = [float(v) for v in values]
            print(f"  prices: {values_float}")
            if len(values_float) > 20:
                print(f"  prices (first 10): {values_float[:10]}")
                print(f"  prices (last 10): {values_float[-10:]}")
        else:
            print(f"  prices: []")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)
    
    return results


def test_scan_price_search_with_sample():
    """
    Test với sample data nhỏ (hardcoded)
    """
    print("=" * 80)
    print("TEST: scan_price_search (with sample data)")
    print("=" * 80)
    
    # Sample data từ log
    sample_log = """
[2025.11.08-20.21.00:708][609]GameLog: Display: [Game] ----Socket RecvMessage STT----XchgSearchPrice----SynId = 64158
[2025.11.08-20.21.00:708][609]GameLog: Display: [Game] 
+errCode
+prices+1+unitPrices+1 [0.18004866180049]
|      | |          +2 [0.18008048289738]
|      | |          +3 [0.18012422360248]
|      | |          +4 [0.18014705882353]
|      | |          +5 [0.18015665796345]
|      | |          +6 [0.18018018018018]
|      | |          +7 [0.18018018018018]
|      | |          +8 [0.18018018018018]
|      | |          +9 [0.18018018018018]
|      | |          +10 [0.18018018018018]
|      | |          +100 [0.18018018018018]
|      | +currency [100300]
|      +2+unitPrices+1 [20000.0]
|      | |          +2 [30000.0]
|      +currency [100200]
[2025.11.08-20.21.00:708][609]GameLog: Display: [Game] ----Socket RecvMessage End----
XchgSearchPrice----SynId = 64158 +refer [5028]
"""
    
    print("Sample log data:")
    print(sample_log)
    print("-" * 80)
    
    # Test scan
    results = scan_price_search(sample_log)
    
    # Hiển thị kết quả
    print(f"\nFound {len(results)} price search result(s)")
    for idx, result in enumerate(results, 1):
        print(f"\nResult #{idx}:")
        print(f"  synId: {result.get('synId')}")
        print(f"  itemId: {result.get('itemId')}")
        print(f"  values_count: {len(result.get('values', []))}")
        print(f"  average_price: {result.get('average_price')}")
        print(f"  highest_price: {result.get('highest_price')}")
        
        values = result.get('values', [])
        if values:
            values_float = [float(v) for v in values]
            print(f"  prices: {values_float}")
    
    print("\n" + "=" * 80)
    return results


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEST SCAN_PRICE_SEARCH")
    print("=" * 80 + "\n")
    
    # Test 1: Với sample data hardcoded
    print("\n[TEST 1] Testing with hardcoded sample data...")
    test_scan_price_search_with_sample()
    
    # Test 2: Với data từ UE_game.log (nếu file tồn tại)
    log_file = "UE_game.log"
    if os.path.exists(log_file):
        print(f"\n[TEST 2] Testing with data from {log_file}...")
        # Tìm một phần log có chứa XchgSearchPrice để test
        # Đọc khoảng 500 dòng từ dòng 403800 (có chứa XchgSearchPrice)
        test_scan_price_search_from_file(log_file, start_line=403800, end_line=404300)
    else:
        print(f"\n[TEST 2] Skipped: {log_file} not found")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
