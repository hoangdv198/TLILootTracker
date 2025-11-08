"""
Item Service Module
===================

Mục đích:
    Module này cung cấp các service functions để lấy thông tin item từ itemId:
    - get_item_info(): Lấy thông tin đầy đủ của item (name, type, price)
    - Có cache để tối ưu performance

Tác dụng:
    - Centralized logic để lấy thông tin item
    - Tối ưu performance với cache
    - Dễ maintain và extend
    - Cung cấp interface rõ ràng cho các module khác sử dụng
"""
import json
import os
import time
from typing import Dict, Optional


# Cache để tránh đọc file nhiều lần
_id_table_cache = None
_id_table_cache_time = 0
_price_log_cache = None
_price_log_cache_time = 0
_cache_ttl = 5  # Cache 5 giây


def _load_id_table() -> Dict:
    """
    Load id_table.json với cache
    
    Returns:
        Dict: Dictionary với format {itemId: {name: str, type: str}}
    """
    global _id_table_cache, _id_table_cache_time
    
    now = time.time()
    if _id_table_cache is None or (now - _id_table_cache_time > _cache_ttl):
        try:
            with open("id_table.json", 'r', encoding="utf-8") as f:
                id_table_data = json.load(f)
            
            # Transform thành format dễ dùng: {itemId: {name, type}}
            _id_table_cache = {}
            for item_id, item_data in id_table_data.items():
                if isinstance(item_data, dict):
                    _id_table_cache[str(item_id)] = {
                        "name": item_data.get("name", f"Item {item_id}"),
                        "type": item_data.get("type", "Unknown")
                    }
                else:
                    # Fallback nếu format không đúng
                    _id_table_cache[str(item_id)] = {
                        "name": str(item_data),
                        "type": "Unknown"
                    }
            
            _id_table_cache_time = now
        except Exception as e:
            print(f'Error reading id_table.json: {e}')
            if _id_table_cache is None:
                _id_table_cache = {}
    
    return _id_table_cache


def _load_price_log() -> Dict:
    """
    Load search_price_log.json với cache
    
    Returns:
        Dict: Dictionary với format {itemId: price}
    """
    global _price_log_cache, _price_log_cache_time
    
    now = time.time()
    if _price_log_cache is None or (now - _price_log_cache_time > _cache_ttl):
        try:
            with open("search_price_log.json", 'r', encoding="utf-8") as f:
                price_log = json.load(f)
            
            # Transform thành format dễ dùng: {itemId: price}
            _price_log_cache = {}
            for entry in price_log:
                item_id = entry.get("idItem")
                price = entry.get("price", 0)
                if item_id:
                    _price_log_cache[str(item_id)] = price
            
            _price_log_cache_time = now
        except Exception as e:
            print(f'Error reading search_price_log.json: {e}')
            if _price_log_cache is None:
                _price_log_cache = {}
    
    return _price_log_cache


def get_item_info(item_id: str, apply_tax: bool = False) -> Dict[str, any]:
    """
    Lấy thông tin đầy đủ của item từ itemId
    
    Args:
        item_id (str): Item ID cần lấy thông tin
        apply_tax (bool): Có áp dụng tax 12.5% không (default: False)
                         Tax chỉ áp dụng cho items khác 100300
    
    Returns:
        Dict: Dictionary chứa thông tin item:
        {
            "itemId": "100300",
            "name": "Memory Fragments",
            "type": "Hard Currency",
            "price": 0.0,
            "price_with_tax": 0.0  # Nếu apply_tax=True
        }
        
        Nếu không tìm thấy item:
        {
            "itemId": "100300",
            "name": "Item 100300",
            "type": "Unknown",
            "price": 0.0,
            "price_with_tax": 0.0
        }
    """
    item_id_str = str(item_id)
    
    # Load id_table và price_log
    id_table = _load_id_table()
    price_log = _load_price_log()
    
    # Lấy name và type từ id_table
    item_data = id_table.get(item_id_str, {})
    if not item_data:
        # Fallback nếu không tìm thấy
        item_data = {
            "name": f"Item {item_id_str}",
            "type": "Unknown"
        }
    
    name = item_data.get("name", f"Item {item_id_str}")
    item_type = item_data.get("type", "Unknown")
    
    # Lấy price từ price_log (đã được làm tròn 4 chữ số)
    price = price_log.get(item_id_str, 0.0)
    
    # Tính price_with_tax nếu cần và làm tròn về 4 chữ số thập phân
    price_with_tax = price
    if apply_tax and item_id_str != "100300":
        price_with_tax = price * 0.875  # Tax 12.5%
    
    # Làm tròn tất cả giá trị về 4 chữ số thập phân
    price = round(price, 4) if price > 0 else 0.0
    price_with_tax = round(price_with_tax, 4) if price_with_tax > 0 else 0.0
    
    return {
        "itemId": item_id_str,
        "name": name,
        "type": item_type,
        "price": price,
        "price_with_tax": price_with_tax
    }


def get_item_name(item_id: str) -> str:
    """
    Lấy name của item từ itemId (shortcut function)
    
    Args:
        item_id (str): Item ID cần lấy name
    
    Returns:
        str: Item name, hoặc "Item {itemId}" nếu không tìm thấy
    """
    info = get_item_info(item_id)
    return info.get("name", f"Item {item_id}")


def get_item_price(item_id: str, apply_tax: bool = False) -> float:
    """
    Lấy price của item từ itemId (shortcut function)
    
    Args:
        item_id (str): Item ID cần lấy price
        apply_tax (bool): Có áp dụng tax 12.5% không (default: False)
    
    Returns:
        float: Item price (đã apply tax nếu cần)
    """
    info = get_item_info(item_id, apply_tax=apply_tax)
    if apply_tax:
        return info.get("price_with_tax", 0.0)
    return info.get("price", 0.0)


def clear_cache():
    """
    Clear cache để force reload data từ file
    
    Useful khi muốn đảm bảo data mới nhất
    """
    global _id_table_cache, _id_table_cache_time, _price_log_cache, _price_log_cache_time
    _id_table_cache = None
    _id_table_cache_time = 0
    _price_log_cache = None
    _price_log_cache_time = 0

