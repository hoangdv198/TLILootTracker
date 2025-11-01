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
from drop_handler import deal_change
from price_handler import get_price_info


class MyThread(threading.Thread):
    """Thread for monitoring log file and processing updates"""
    history = ""
    
    def run(self):
        import config
        import index as main_module
        
        self.history = open(config.position_log, "r", encoding="utf-8")
        self.history.seek(0, 2)
        while True:
            try:
                time.sleep(1)
                things = self.history.read()
                # print(things)
                deal_change(things)
                get_price_info(things)
                
                # Sync global state from drop_handler to main module
                from drop_handler import drop_list as dh_drop_list, drop_list_all as dh_drop_list_all, income as dh_income, income_all as dh_income_all
                main_module.drop_list = dh_drop_list
                main_module.drop_list_all = dh_drop_list_all
                main_module.income = dh_income
                main_module.income_all = dh_income_all
                
                if main_module.is_in_map:
                    m = int((time.time() - main_module.t) // 60)
                    s = int((time.time() - main_module.t) % 60)
                    main_module.root.label_current_time.config(text=f"Current: {m}m{s}s")
                    main_module.root.label_current_speed.config(text=f"🔥 {round(main_module.income / ((time.time() - main_module.t) / 60), 2)} /min")
                    tmp_total_time = main_module.total_time + (time.time() - main_module.t)
                    m = int(tmp_total_time // 60)
                    s = int(tmp_total_time % 60)
                    main_module.root.label_total_time.config(text=f"Total: {m}m{s}s")
                    main_module.root.label_total_speed.config(text=f"🔥 {round(main_module.income_all / (tmp_total_time / 60), 2)} /min")
                else:
                    main_module.t = time.time()
            except Exception as e:
                print("-------------Error-----------")
                # Output error line number
                import traceback
                traceback.print_exc()

