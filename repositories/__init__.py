"""
Repositories Package
===================

Package này chứa tất cả các repository/client để giao tiếp với external APIs và data sources.

Repositories chỉ chịu trách nhiệm:
- Giao tiếp với external APIs
- HTTP requests/responses
- Data transformation cơ bản (JSON parsing)
- Không chứa business logic
"""

from .price_api_client import (
    fetch_all_prices,
    fetch_item_by_id,
    submit_price,
    register_user
)

__all__ = [
    'fetch_all_prices',
    'fetch_item_by_id',
    'submit_price',
    'register_user'
]

