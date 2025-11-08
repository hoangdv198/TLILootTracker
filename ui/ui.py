"""
UI Components Module
====================

Mục đích:
    Module này chứa tất cả các UI components cho ứng dụng:
    - Main window với thống kê cơ bản
    - Drops panel window
    - Settings panel window
    - Tất cả các UI elements và event handlers

Tác dụng:
    - Tạo và quản lý giao diện người dùng (Tkinter)
    - Xử lý user interactions
    - Hiển thị thống kê drops, income, time
    - Quản lý settings UI

Class chính:
    - App: Main application window và UI components
"""
import time
import json
import ctypes
from tkinter import *
from tkinter.ttk import *
from tkinter import ttk
from app import state
from app import config


class App(Tk):
    """Main application window with all UI components"""
    show_type = ["Compass","Hard Currency","Special Items","Memory Materials","Equipment Materials","Gameplay Tickets","Map Tickets","Cube Materials","Erosion Materials","Dream Materials","Tower Materials","BOSS Tickets","Memory Fluorescence","Divine Seal","Overlap Materials"]
    # Correct, Circle, Wrong
    status = ["✔", "◯", "✘"]
    cost = 0
    
    # Cache data để tránh đọc file nhiều lần
    _id_table_cache = None
    _id_table_cache_time = 0
    _price_log_cache = None
    _price_log_cache_time = 0
    _cache_ttl = 5  # Cache 5 giây
    
    def __init__(self):
        super().__init__()
        self.title("FurTorch v0.0.1a4")
        self.geometry()

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # Call API to get current scale factor
        ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        # Set scale factor
        self.tk.call('tk', 'scaling', ScaleFactor / 75)
        basic_frame = ttk.Frame(self)
        advanced_frame = ttk.Frame(self)
        basic_frame.pack(side="top", fill="both")
        advanced_frame.pack(side="top", fill="both")
        self.basic_frame = basic_frame
        self.advanced_frame = advanced_frame
        # Remove window maximize button
        self.resizable(False, False)
        # Remove window minimize button
        self.attributes('-toolwindow', True)
        # Set red
        basic_frame.config(style="Red.TFrame")
        advanced_frame.config(style="Blue.TFrame")
        style = ttk.Style()
        #style.configure("Red.TFrame", background="#ffcccc")
        #style.configure("Blue.TFrame", background="#ccccff")
        label_current_time = ttk.Label(basic_frame, text="Current: 0m00s", font=("黑体", 14), anchor="w")
        label_current_time.grid(row=0, column=0, padx = 5, sticky="w")
        label_current_speed = ttk.Label(basic_frame, text="🔥 0 /min", font=("黑体", 14))
        label_current_speed.grid(row=0, column=2, sticky="e", padx = 5)
        label_total_time = ttk.Label(basic_frame, text="Total: 00m00s", font=("黑体", 14), anchor="w")
        label_total_time.grid(row=1, column=0, padx = 5, sticky="w")
        label_total_speed = ttk.Label(basic_frame, text="🔥 0 /min", font=("黑体", 14))
        label_total_speed.grid(row=1, column=2, sticky="e", padx = 5)
        self.label_current_time = label_current_time
        self.label_current_speed = label_current_speed
        self.label_total_time = label_total_time
        self.label_total_speed = label_total_speed
        # A line
        separator = ttk.Separator(basic_frame, orient='horizontal')
        separator.grid(row=2, columnspan=3, sticky="ew", pady=5)
        # Label occupies two cells
        label_current_earn = ttk.Label(basic_frame, text="🔥 0", font=("Algerian", 20, "bold"))
        label_current_earn.grid(row=3, column=0, padx=5)
        label_map_count = ttk.Label(basic_frame, text="🎫 0", font=("黑体", 14))
        label_map_count.grid(row=3, column=1, padx=5)
        # Button occupies one cell
        words_short = StringVar()
        words_short.set("Current Map")
        self.words_short = words_short
        button_show_advanced = ttk.Button(basic_frame, textvariable=words_short)
        button_show_advanced.grid(row=3, column=2, padx=5)
        button_show_advanced.config(command=self.change_states)
        self.label_current_earn = label_current_earn
        self.label_map_count = label_map_count
        self.button_show_advanced = button_show_advanced

        # Buttons: Drops, Filter, Log, Settings (height and width equal)
        button_drops = ttk.Button(advanced_frame, text="Drops", width=7)
        button_filter = ttk.Button(advanced_frame, text="Filter", width=7)
        button_log = ttk.Button(advanced_frame, text="Log", width=7)
        button_settings = ttk.Button(advanced_frame, text="Settings", width=7)
        button_drops.grid(row=0, column=0, padx=5, ipady=10)
        button_filter.grid(row=0, column=1, padx=5, ipady=10)
        button_log.grid(row=0, column=2, padx=5, ipady=10)
        button_settings.grid(row=0, column=3, padx=5, ipady=10)
        # Four new windows
        self.button_drops = button_drops
        self.button_filter = button_filter
        self.button_log = button_log
        self.button_settings = button_settings

        self.button_settings.config(command=self.show_settings, cursor="hand2")
        self.button_drops.config(command=self.show_diaoluo, cursor="hand2")

        self.inner_pannel_drop = Toplevel(self)
        self.inner_pannel_drop.title("Drops")
        self.inner_pannel_drop.geometry()
        # Hide maximize and minimize buttons
        self.inner_pannel_drop.resizable(False, False)
        self.inner_pannel_drop.attributes('-toolwindow', True)
        # Move to right side of main window
        self.inner_pannel_drop.geometry('+0+0')
        # Hide window ngay sau khi tạo để tránh hiển thị
        self.inner_pannel_drop.withdraw()
        inner_pannel_drop_left = ttk.Frame(self.inner_pannel_drop)
        inner_pannel_drop_left.grid(row=0, column=0)
        words = StringVar()
        words.set("Current: Current Map Drops Click to Switch to Total Drops")
        inner_pannel_drop_show_all = ttk.Button(self.inner_pannel_drop, textvariable=words, width=30)
        inner_pannel_drop_show_all.grid(row=0, column=1)
        self.words = words
        self.inner_pannel_drop_show_all = inner_pannel_drop_show_all
        self.inner_pannel_drop_show_all.config(cursor="hand2", command=self.change_states)
        inner_pannel_drop_right = ttk.Frame(self.inner_pannel_drop)
        inner_pannel_drop_right.grid(row=1, column=1, rowspan=5)
        inner_pannel_drop_total = ttk.Button(self.inner_pannel_drop, text="All", width=7)
        inner_pannel_drop_total.grid(row=0, column=0, padx=5, ipady=10)
        inner_pannel_drop_tonghuo = ttk.Button(self.inner_pannel_drop, text="Currency", width=7)
        inner_pannel_drop_tonghuo.grid(row=1, column=0, padx=5, ipady=10)
        inner_pannel_drop_huijing = ttk.Button(self.inner_pannel_drop, text="Ash", width=7)
        inner_pannel_drop_huijing.grid(row=2, column=0, padx=5, ipady=10)
        inner_pannel_drop_luopan = ttk.Button(self.inner_pannel_drop, text="Compass", width=7)
        inner_pannel_drop_luopan.grid(row=3, column=0, padx=5, ipady=10)
        inner_pannel_drop_yingguang = ttk.Button(self.inner_pannel_drop, text="Fluorescence", width=7)
        inner_pannel_drop_yingguang.grid(row=4, column=0, padx=5, ipady=10)
        inner_pannel_drop_qita = ttk.Button(self.inner_pannel_drop, text="Others", width=7)
        inner_pannel_drop_qita.grid(row=5, column=0, padx=5, ipady=10)
        self.inner_pannel_drop_total = inner_pannel_drop_total
        self.inner_pannel_drop_tonghuo = inner_pannel_drop_tonghuo
        self.inner_pannel_drop_huijing = inner_pannel_drop_huijing
        self.inner_pannel_drop_luopan = inner_pannel_drop_luopan
        self.inner_pannel_drop_yingguang = inner_pannel_drop_yingguang
        self.inner_pannel_drop_qita = inner_pannel_drop_qita
        self.inner_pannel_drop_total.config(command=self.show_all_type, cursor="hand2")
        self.inner_pannel_drop_tonghuo.config(command=self.show_tonghuo, cursor="hand2")
        self.inner_pannel_drop_huijing.config(command=self.show_huijing, cursor="hand2")
        self.inner_pannel_drop_luopan.config(command=self.show_luopan, cursor="hand2")
        self.inner_pannel_drop_yingguang.config(command=self.show_yingguang, cursor="hand2")
        self.inner_pannel_drop_qita.config(command=self.show_qita, cursor="hand2")
        # Vertical scrollbar
        self.inner_pannel_drop_scrollbar = Scrollbar(inner_pannel_drop_right)
        self.inner_pannel_drop_scrollbar.config(orient=VERTICAL)
        self.inner_pannel_drop_scrollbar.pack(side=RIGHT, fill=Y)
        self.inner_pannel_drop_listbox = Listbox(inner_pannel_drop_right, yscrollcommand=self.inner_pannel_drop_scrollbar.set, width=50, height=20)
        self.inner_pannel_drop_listbox.pack(side=LEFT, fill=BOTH)
        self.inner_pannel_drop_scrollbar.config(command=self.inner_pannel_drop_listbox.yview)
        self.inner_pannel_drop_listbox.insert(END, f"{self.status[0]} <3min {self.status[1]} <15min {self.status[2]} >15min")
        # Set row height
        self.inner_pannel_drop_listbox.config(font=("Consolas", 12))
        # Set width
        self.inner_pannel_drop_listbox.config(width=30)

        # Settings page
        self.inner_pannel_settings = Toplevel(self)
        self.inner_pannel_settings.title("Settings")
        self.inner_pannel_settings.geometry()
        # Hide maximize and minimize buttons
        self.inner_pannel_settings.resizable(False, False)
        self.inner_pannel_settings.attributes('-toolwindow', True)
        # Move to right side of main window
        self.inner_pannel_settings.geometry('+300+0')
        # Hide window ngay sau khi tạo để tránh hiển thị
        self.inner_pannel_settings.withdraw()
        # Label + Text box
        label_setting_1 = ttk.Label(self.inner_pannel_settings, text="Cost per Map:")
        label_setting_1.grid(row=0, column=0, padx=5, pady=5)
        entry_setting_1 = ttk.Entry(self.inner_pannel_settings)
        entry_setting_1.grid(row=0, column=1, padx=5, pady=5)
        global config_data
        # Choose tax calculation or not
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = f.read()
        config_data = json.loads(config_data)
        chose = ttk.Combobox(self.inner_pannel_settings, values=["No Tax", "With Tax"], state="readonly")
        chose.current(config_data.get("tax", 0))
        chose.grid(row=2, column=1, padx=5, pady=5)
        self.chose = chose
        chose.bind("<<ComboboxSelected>>", lambda event: self.change_tax(self.chose.current()))
        self.label_setting_1 = label_setting_1
        self.entry_setting_1 = entry_setting_1
        # Set opacity
        self.label_setting_2 = ttk.Label(self.inner_pannel_settings, text="Opacity:")
        self.label_setting_2.grid(row=1, column=0, padx=5, pady=5)
        # Slider
        self.scale_setting_2 = ttk.Scale(self.inner_pannel_settings, from_=0.1, to=1.0, orient=HORIZONTAL)
        self.scale_setting_2.grid(row=1, column=1, padx=5, pady=5)
        self.scale_setting_2.config(command=self.change_opacity)
        print(config_data)
        self.entry_setting_1.insert(0, str(config_data["cost_per_map"]))
        self.entry_setting_1.bind("<Return>", lambda event: self.change_cost(self.entry_setting_1.get()))
        self.scale_setting_2.set(config_data["opacity"])
        self.change_opacity(config_data["opacity"])
        self.change_cost(config_data["cost_per_map"])
        # Đảm bảo cả 2 windows đều bị ẩn khi khởi động (đã withdraw ở trên, nhưng gọi lại để chắc chắn)
        self.inner_pannel_drop.withdraw()
        self.inner_pannel_settings.withdraw()
        self.inner_pannel_drop.protocol("WM_DELETE_WINDOW", self.close_diaoluo)
        self.inner_pannel_settings.protocol("WM_DELETE_WINDOW", self.close_settings)
        # Always on top
        self.attributes('-topmost', True)
        self.inner_pannel_drop.attributes('-topmost', True)
        self.inner_pannel_settings.attributes('-topmost', True)
    
    def change_tax(self, value):
        global config_data
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = f.read()
        config_data = json.loads(config_data)
        config_data["tax"] = int(value)
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

    def change_states(self):
        """Switch giữa Current Map và Total Drops view"""
        state.show_all = not state.show_all
        if not state.show_all:
            self.words.set("Current: Current Map Drops Click to Switch to Total Drops")
            self.words_short.set("Current Map")
        else:
            self.words.set("Current: Total Drops Click to Switch to Current Map Drops")
            self.words_short.set("Total Drops")
        self.reshow()
    
    def change_cost(self, value):
        value = str(value)
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = f.read()
        config_data = json.loads(config_data)
        config_data["cost_per_map"] = float(value)
        with open("config.json", "w", encoding="utf-8") as f:
            print(config_data)
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        self.cost = float(value)
    
    def show_diaoluo(self):
        this = self.inner_pannel_drop
        # Check if window is hidden
        if this.state() == "withdrawn":
            this.deiconify()
        else:
            this.withdraw()

    def close_diaoluo(self):
        self.inner_pannel_drop.withdraw()

    def close_settings(self):
        try:
            value = float(self.entry_setting_1.get())
            self.change_cost(value)
        except:
            pass
        self.inner_pannel_settings.withdraw()

    def show_settings(self):
        this = self.inner_pannel_settings
        if this.state() == "withdrawn":
            this.deiconify()
        else:
            this.withdraw()

    def change_opacity(self, value):
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = f.read()
        config_data = json.loads(config_data)
        config_data["opacity"] = float(value)
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        self.attributes('-alpha', float(value))
        self.inner_pannel_drop.attributes('-alpha', float(value))
        self.inner_pannel_settings.attributes('-alpha', float(value))
    
    def reshow(self):
        """
        Rerender/Reload UI - Refresh drops list và các labels
        
        Chức năng:
            - Load data từ id_table.json và search_price_log.json (với cache)
            - Update labels: map_count, current_earn
            - Xóa và render lại toàn bộ drops list trong listbox
            - Hiển thị items theo filter (show_type)
            - Tính toán status (✔/◯/✘) dựa trên last_update time
        
        Được gọi khi:
            - Có drops mới (từ drop_handler.py)
            - User thay đổi filter (show_all_type, show_tonghuo, ...)
            - User switch giữa Current Map và Total Drops
        
        Note: Hàm này được schedule từ main thread qua root.after() để tránh blocking
        """
        # Load id_table.json với cache để tránh đọc file nhiều lần
        now = time.time()
        if (self._id_table_cache is None or 
            now - self._id_table_cache_time > self._cache_ttl):
            try:
                with open("id_table.json", 'r', encoding="utf-8") as f:
                    self._id_table_cache = json.load(f)
                    self._id_table_cache_time = now
            except Exception as e:
                print(f'Error reading id_table.json: {e}')
                if self._id_table_cache is None:
                    self._id_table_cache = {}
        
        id_table = self._id_table_cache
        
        # Load search_price_log.json với cache để tránh đọc file nhiều lần
        price_log_dict = {}
        if (self._price_log_cache is None or 
            now - self._price_log_cache_time > self._cache_ttl):
            try:
                with open("search_price_log.json", 'r', encoding="utf-8") as f:
                    price_log = json.load(f)
                self._price_log_cache = {}
                for entry in price_log:
                    item_id = entry.get("idItem")
                    if item_id:
                        self._price_log_cache[str(item_id)] = {
                            "price": entry.get("price", 0),
                            "last_update": entry.get("last_update", 0)
                        }
                self._price_log_cache_time = now
            except Exception as e:
                print(f'Error reading search_price_log.json: {e}')
                if self._price_log_cache is None:
                    self._price_log_cache = {}
        
        price_log_dict = self._price_log_cache
        
        # Update labels: map count và current earnings
        self.label_map_count.config(text=f"🎫 {state.map_count}")
        if state.show_all:
            tmp = state.drop_list_all
            self.label_current_earn.config(text=f"🔥 {round(state.income_all, 2)}")
        else:
            tmp = state.drop_list
            self.label_current_earn.config(text=f"🔥 {round(state.income, 2)}")
        
        # Xóa toàn bộ items cũ trong listbox (giữ lại header ở index 0)
        self.inner_pannel_drop_listbox.delete(1, END)
        
        # Render lại từng item trong drops list
        for i in tmp.keys():
            item_id = str(i)
            
            # Lấy name và type từ id_table.json
            item_data = id_table.get(item_id, {})
            item_name = item_data.get("name", f"Item {item_id}")
            item_type = item_data.get("type", "Unknown")
            
            # Filter theo show_type (skip items không match filter)
            if item_type not in self.show_type:
                continue
            
            # Lấy price và last_update từ search_price_log.json
            price_data = price_log_dict.get(item_id, {})
            now = time.time()
            last_time = price_data.get("last_update", 0)
            time_passed = now - last_time
            
            # Tính status dựa trên thời gian update:
            # ✔ = < 3 phút (fresh), ◯ = 3-15 phút (stale), ✘ = > 15 phút (outdated)
            if time_passed < 180:
                status = self.status[0]  # ✔
            elif time_passed < 900:
                status = self.status[1]  # ◯
            else:
                status = self.status[2]  # ✘
            
            # Tính giá (apply tax nếu có)
            item_price = price_data.get("price", 0)
            if config.config_data.get("tax", 0) == 1 and item_id != "100300":
                item_price = item_price * 0.875  # Apply 12.5% tax
            
            # Insert item vào listbox: status + name + quantity + total value
            self.inner_pannel_drop_listbox.insert(END, f"{status} {item_name} x{tmp[i]} [{tmp[i] * item_price}]")

    def show_all_type(self):
        self.show_type = ["Compass","Hard Currency","Special Items","Memory Materials","Equipment Materials","Gameplay Tickets","Map Tickets","Cube Materials","Erosion Materials","Dream Materials","Tower Materials","BOSS Tickets","Memory Fluorescence","Divine Seal","Overlap Materials"]
        self.reshow()
    
    def show_tonghuo(self):
        self.show_type = ["Hard Currency"]
        self.reshow()
    
    def show_huijing(self):
        self.show_type = ["Equipment Materials"]
        self.reshow()
    
    def show_luopan(self):
        self.show_type = ["Compass"]
        self.reshow()
    
    def show_yingguang(self):
        self.show_type = ["Memory Fluorescence"]
        self.reshow()
    
    def show_qita(self):
        self.show_type = ["Special Items","Memory Materials","Gameplay Tickets","Map Tickets","Cube Materials","Erosion Materials","Dream Materials","Tower Materials","BOSS Tickets","Divine Seal","Overlap Materials"]
        self.reshow()

