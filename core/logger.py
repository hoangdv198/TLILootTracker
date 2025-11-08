"""
Logger Utility Module
=====================

Mục đích:
    Module này cung cấp utility functions cho logging trong ứng dụng.

Tác dụng:
    - Cung cấp logger function có thể tái sử dụng
    - Format thời gian nhất quán
    - Ghi log ra cả console và file logger.txt
    - Dễ dàng thay đổi format log trong tương lai

Function chính:
    - log_debug(): Log message với prefix [DEBUG] và timestamp
"""
from datetime import datetime

# File path cho log file
LOG_FILE = "logger.txt"


def log_debug(message):
    """
    Logger utility function - Log message với prefix [DEBUG] và timestamp
    
    Chỉ log các thông tin quan trọng:
    - Drop items được nhặt
    - Errors và warnings
    - Map entry/exit (nếu cần)
    
    Args:
        message (str): Message cần log
    
    Format output: [DEBUG] MM-DD-YYYY hh:mm:ss - {message}
    
    Example:
        log_debug("drop item 360404")
        # Output: [DEBUG] 01-15-2025 23:13:40 - drop item 360404
        # (cả console và file logger.txt)
    """
    
    timestamp = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    log_message = f"[DEBUG] {timestamp} - {message}"
    
    # Print ra console
    print(log_message)
    
    # Ghi vào file logger.txt
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    except Exception as e:
        # Nếu không ghi được file, chỉ print ra console
        print(f"[ERROR] Failed to write to {LOG_FILE}: {e}")

