"""
Price API Client
================

Repository này chịu trách nhiệm giao tiếp với Price API server.
Chỉ chứa các HTTP requests/responses, không có business logic.

Các API endpoints:
    - GET /get: Lấy toàn bộ dữ liệu giá từ server
    - GET /gowork?id={item_id}: Lấy thông tin item cụ thể
    - GET /update: Gửi giá mới lên server
    - GET /reg: Đăng ký user mới
"""
import requests as rq

SERVER = "serverp.furtorch.heili.tech"
TIMEOUT = 10


def fetch_all_prices():
    """
    Lấy toàn bộ dữ liệu giá từ server
    
    Returns:
        dict: Dữ liệu giá từ server dưới dạng JSON
    
    Raises:
        requests.RequestException: Nếu request thất bại
    """
    try:
        response = rq.get(f"http://{SERVER}/get", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching all prices: {e}")
        raise


def fetch_item_by_id(item_id):
    """
    Lấy thông tin item cụ thể từ server
    
    Args:
        item_id (str): ID của item cần lấy
    
    Returns:
        dict: Thông tin item từ server dưới dạng JSON
    
    Raises:
        requests.RequestException: Nếu request thất bại
    """
    try:
        response = rq.get(f"http://{SERVER}/gowork?id={item_id}", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching item {item_id}: {e}")
        raise


def submit_price(ids, price, user):
    """
    Gửi giá mới lên server
    
    Args:
        ids (str): ID của item
        price (float): Giá mới
        user (str): User ID
    
    Returns:
        dict: Response từ server hoặc None nếu lỗi
    """
    print(price)
    try:
        response = rq.get(
            f"http://{SERVER}/update?user={user}&ids={ids}&new_price={price}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        print(result)
        return result
    except Exception as e:
        print(e)
        return None


def register_user():
    """
    Đăng ký user mới trên server
    
    Returns:
        dict: Response chứa user_id
    
    Raises:
        requests.RequestException: Nếu request thất bại
    """
    try:
        response = rq.get(f"http://{SERVER}/reg", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error registering user: {e}")
        raise

