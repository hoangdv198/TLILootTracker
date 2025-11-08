"""
Price Handler Module
====================

Mục đích:
    Module này là wrapper/adapter để tương thích với code cũ.
    Business logic đã được di chuyển vào services/price_service.py
    
Lưu ý: 
    - Các API calls đã được di chuyển vào repositories/price_api_client.py
    - Business logic đã được di chuyển vào services/price_service.py
    - Module này chỉ re-export để backward compatibility
"""
from services.price_service import get_price_info, price_update

# Re-export để backward compatibility
__all__ = ['get_price_info', 'price_update']



