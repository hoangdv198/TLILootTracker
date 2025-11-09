"""
Application Thread Management Module
====================================

Mục đích:
    Module này chứa thread management cho ứng dụng:
    - Thread đọc log file real-time
    - Xử lý và cập nhật UI khi có changes

Tác dụng:
    - Monitor log file mỗi 1 giây và xử lý updates
    - Sync state từ drop_handler vào main module
    - Cập nhật UI real-time với thời gian và tốc độ kiếm được

Class chính:
    - MyThread: Background thread đọc và xử lý log file
"""
import time
import threading
from core.drop_handler import deal_change
from core.price_handler import get_price_info
from app import state
from app import config
from core.drop_handler import (
    drop_list as dh_drop_list,
    drop_list_all as dh_drop_list_all,
    income as dh_income,
    income_all as dh_income_all
)
from services.log_scan_service import scan_init_bag


class MyThread(threading.Thread):
    """Thread for monitoring log file and processing updates"""
    history = ""
    
    def _update_ui_labels(self, m, s, total_m, total_s):
        """Update UI labels từ main thread (được gọi qua root.after())"""
        try:
            if not state.root or not state.root.winfo_exists():
                return
            
            # Update labels từ main thread (an toàn)
            state.root.label_current_time.config(text=f"Current: {m}m{s}s")
            
            current_speed = round(state.income / ((time.time() - state.t) / 60), 2) if (time.time() - state.t) > 0 else 0
            state.root.label_current_speed.config(text=f"🔥 {current_speed} /min")
            
            state.root.label_total_time.config(text=f"Total: {total_m}m{total_s}s")
            
            total_time_elapsed = (state.total_time + (time.time() - state.t)) / 60
            total_speed = round(state.income_all / total_time_elapsed, 2) if total_time_elapsed > 0 else 0
            state.root.label_total_speed.config(text=f"🔥 {total_speed} /min")
        except Exception:
            # Widget đã bị destroy, bỏ qua
            pass
    
    def run(self):
        """
        Main thread loop - đọc log file và xử lý updates
        
        Note: Import traceback trong except block là OK theo PEP 8
        vì chỉ dùng khi có exception (lazy loading)
        """
        self.history = open(config.position_log, "r", encoding="utf-8")
        self.history.seek(0, 2)
        while True:
            try:
                time.sleep(1)
                things = self.history.read()
                # print(things)
                
                # scan_init_bag: Tracking liên tục init bag events để update state.bag_items
                # Nếu track được event init bag, sẽ update state.bag_items với data mới
                scan_init_bag(things)
                
                # deal_change: Xử lý drops từ log - phát hiện vào/ra map, scan drops, cập nhật statistics và UI
                deal_change(things)
                # get_price_info: Extract giá từ exchange search results trong log
                get_price_info(things)
                
                # Sync global state from drop_handler to state module
                state.drop_list = dh_drop_list
                state.drop_list_all = dh_drop_list_all
                state.income = dh_income
                state.income_all = dh_income_all
                
                # Schedule UI update từ main thread để tránh blocking và lỗi Tkinter
                if state.is_in_map:
                    m = int((time.time() - state.t) // 60)
                    s = int((time.time() - state.t) % 60)
                    tmp_total_time = state.total_time + (time.time() - state.t)
                    total_m = int(tmp_total_time // 60)
                    total_s = int(tmp_total_time % 60)
                    
                    # Dùng root.after() để schedule update từ main thread (không block)
                    try:
                        if state.root and state.root.winfo_exists():
                            state.root.after(0, lambda m=m, s=s, tm=total_m, ts=total_s: self._update_ui_labels(
                                m, s, tm, ts
                            ))
                    except (RuntimeError, AttributeError):
                        # Main loop đã kết thúc, exit thread
                        break
                else:
                    state.t = time.time()
            except Exception as e:
                print("-------------Error-----------")
                # Import traceback trong except block là OK (lazy loading khi có exception)
                import traceback
                traceback.print_exc()

