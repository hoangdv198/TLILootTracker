"""
Global State Module
===================

Mục đích:
    Module này chứa tất cả global state variables để tránh circular imports.
    Thay vì import index.py từ ui.py, các module sẽ import state từ đây.

Tác dụng:
    - Tránh circular imports giữa index.py và ui.py
    - Centralized state management
    - Dễ test và maintain hơn
"""

# Global state variables
is_in_map = False
drop_list = {}
drop_list_all = {}
income = 0
income_all = 0
t = None
show_all = False
total_time = 0
map_count = 0
root = None
map_start_time = None  # Thời gian bắt đầu map để tính duration

