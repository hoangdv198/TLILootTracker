"""
Configuration Module
====================

Mục đích:
    Module này xử lý tất cả các cấu hình và khởi tạo ban đầu:
    - Tạo và load config.json
    - Tìm game process và đường dẫn log file
    - Chuẩn bị môi trường cho ứng dụng

Tác dụng:
    - Khởi tạo config.json nếu chưa tồn tại
    - Tìm cửa sổ game "Torchlight: Infinite"
    - Xác định đường dẫn đến file log UE_game.log
    - Verify và prepare log file để đọc

Các biến export:
    - config_data: Dictionary chứa cấu hình (cost_per_map, opacity, tax, user)
    - position_log: Đường dẫn đến file log của game
"""
import os
import json
import psutil
import win32gui
import win32process


# Initialize config file if it doesn't exist
if os.path.exists("config.json") == False:
    with open("config.json", "w", encoding="utf-8") as f:
        config_data = {
            "cost_per_map": 0,
            "opacity": 1.0,
            "tax": 0,
        }
        json.dump(config_data, f, ensure_ascii=False, indent=4)

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    config_data = json.load(f)

# Find game process and log file path
hwnd = win32gui.FindWindow(None, "Torchlight: Infinite  ")
tid, pid = win32process.GetWindowThreadProcessId(hwnd)
process = psutil.Process(pid)
position_game = process.exe()
position_log = position_game + "/../../../TorchLight/Saved/Logs/UE_game.log"
position_log = position_log.replace("\\", "/")
print(position_log)

# Verify log file exists and move to end
with open(position_log, "r", encoding="utf-8") as f:
    print(f.read(100))
    # Move to end of file
    f.seek(0, 2)

