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

# ============================================================================
# Map State Variables
# ============================================================================

# Trạng thái vào/ra map
is_in_map = False  # True khi đang trong map, False khi ở ngoài map

# Thời gian tracking
t = None  # Timestamp khi bắt đầu map hiện tại (dùng để tính duration)
map_start_time = None  # Thời gian bắt đầu map để tính duration (backup)
total_time = 0  # Tổng thời gian đã chơi (tính bằng giây, cộng dồn từ các maps)

# ============================================================================
# Drop Statistics Variables
# ============================================================================

# Danh sách drops của map hiện tại: {item_id: quantity}
# Được reset về {} mỗi khi vào map mới
drop_list = {}

# Danh sách drops tổng cộng (tất cả maps): {item_id: quantity}
# Không reset, cộng dồn từ tất cả các maps
drop_list_all = {}

# ============================================================================
# Income & Profit Variables
# ============================================================================

# Income của map hiện tại (đã trừ cost khi vào map)
# Được reset về -map_cost mỗi khi vào map mới
income = 0

# Tổng income tất cả maps (đã trừ tất cả costs)
# Không reset, cộng dồn từ tất cả các maps
income_all = 0

# Profit của map hiện tại = income (vì income đã trừ cost khi vào map)
# Được reset về -map_cost mỗi khi vào map mới
profit = 0

# Tổng profit tất cả maps (đã trừ tất cả costs)
# Không reset, cộng dồn từ tất cả các maps
profit_all = 0

# ============================================================================
# UI State Variables
# ============================================================================

# Số lượng maps đã chơi (tăng mỗi khi vào map mới)
map_count = 0

# Reference đến main window (Tkinter root)
# Dùng để update UI và lấy cost từ config
root = None

# Trạng thái hiển thị drops: False = Current Map, True = Total Drops
show_all = False

# ============================================================================
# Bag Items State
# ============================================================================

# Dictionary lưu bag items hiện tại trong túi của user
# Format: {item_id_str: {name, pageId, slotId, num}}
# 
# QUAN TRỌNG về flow:
# 1. Khi vào map: scan_init_bag() được gọi để set baseline (số lượng ban đầu)
# 2. Khi có drops: So sánh current_quantity với bag_items[item_id]["num"] để tính new_quantity
# 3. Sau mỗi drop: Update bag_items[item_id]["num"] = current_quantity để track số lượng mới
# 
# Ví dụ:
# - Vào map: bag_items["100300"]["num"] = 770 (baseline)
# - Drop 118: current_quantity = 888, previous = 770, new_quantity = 888 - 770 = 118 ✓
# - Sau drop: bag_items["100300"]["num"] = 888 (update để lần sau so sánh đúng)
bag_items = {}

