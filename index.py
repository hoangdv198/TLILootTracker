"""
Main Entry Point - FurTorch Application
========================================

Mục đích:
    File này là entry point chính của ứng dụng FurTorch.
    Khởi tạo tất cả các module, global variables và start application.

Tác dụng:
    - Import và khởi tạo tất cả các module cần thiết
    - Định nghĩa global state variables
    - Tạo App instance và start UI
    - Khởi chạy các background threads (log monitoring, price update)
    - Start main event loop

Flow khi chạy:
    1. Import các modules (app, drop_handler, price_handler, config)
    2. Khởi tạo global variables (is_in_map, drop_list, income, etc.)
    3. Tạo App instance
    4. Start MyThread để đọc log file
    5. Start price_update thread để sync giá từ server
    6. Chạy mainloop() để hiển thị UI

Lưu ý:
    Chạy file này để start ứng dụng: python index.py
"""
import time
import _thread
from ui.ui import App
from app.app import MyThread
from core.drop_handler import pending_items
from core.price_handler import price_update
from app import config

# Initialize config for drop_handler
from core.drop_handler import config_data as dh_config_data
dh_config_data.update(config.config_data)

# Import state module và initialize
from app import state
state.t = time.time()

# Initialize app
root = App()
root.wm_attributes('-topmost', 1)
state.root = root

# Start log monitoring thread
MyThread().start()

# Export state để backward compatibility (nếu có code cũ còn dùng)
# Các module mới nên import từ app.state thay vì index
is_in_map = state.is_in_map
drop_list = state.drop_list
drop_list_all = state.drop_list_all
income = state.income
income_all = state.income_all
t = state.t
show_all = state.show_all
total_time = state.total_time
map_count = state.map_count

# TODO: Re-enable price sync thread sau khi hoàn thiện
# Start price update thread
# _thread.start_new_thread(lambda: price_update(lambda: pending_items), ())

# Start main loop
root.mainloop()
