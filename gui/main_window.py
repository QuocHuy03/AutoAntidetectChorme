from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QComboBox, QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QTextEdit, QMessageBox, QApplication
)
from core.api_bridge import get_profiles, get_groups, start_profile, close_profile , normalize_profile, update_profile
from core.action_blocks import execute_blocks_from_json
import json, os, threading, time
import pygetwindow as gw
import pyautogui
from qt_material import apply_stylesheet
from PyQt5.QtWidgets import QFileDialog
import pandas as pd
import re
import requests
from threading import Lock


class LogDialog(QDialog):
    def __init__(self, profile_name):
        super().__init__()
        self.setWindowTitle(f"Log - [{profile_name}]")
        layout = QVBoxLayout()
        self.text_edit = QTextEdit(readOnly=True)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        self.resize(600, 400)
        self.log_path = f"logs/{profile_name}.log"
        self.last_content = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_log)
        self.timer.start(1000)
        self.update_log()

    def update_log(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            if new_content != self.last_content:
                scroll_pos = self.text_edit.verticalScrollBar().value()
                self.text_edit.setPlainText(new_content)
                self.text_edit.verticalScrollBar().setValue(scroll_pos)
                self.last_content = new_content
        else:
            self.text_edit.setPlainText("⚠️ Chưa có log cho profile này.")


class ProfileLoaderThread(QThread):
    profiles_loaded = pyqtSignal(list)

    def __init__(self, provider, base_url, group_id):
        super().__init__()
        self.provider = provider
        self.base_url = base_url
        self.group_id = group_id

    def run(self):
        if not self.group_id:
            self.profiles_loaded.emit([])
            return

        profiles = get_profiles(self.provider, self.base_url, self.group_id)
        print(f"[Thread] Fetched {len(profiles)} profiles")
        self.profiles_loaded.emit(profiles)


class ProxyCheckThread(QThread):
    result_signal = pyqtSignal(dict)

    def __init__(self, profile, check_func):
        super().__init__()
        self.profile = profile
        self.check_func = check_func

    def run(self):
        name = self.profile['name']
        proxy = self.profile.get("proxy", "").strip()
        valid = self.check_func(proxy)
        self.result_signal.emit({'name': name, 'valid': valid, 'proxy': proxy})


def load_excel_profiles(excel_path, mode):
    df = pd.read_excel(excel_path)
    profiles = []

    if mode == "profile":
        for _, row in df.iterrows():
            row_data = row.to_dict()
            name = str(row.iloc[0]).strip()
            if name:
                profiles.append({"name": name, "variables": row_data})

    elif mode == "row":
        for idx, row in df.iterrows():
            if row.dropna(how='all').empty:
                continue
            profiles.append({"name": f"Row-{idx+1}", "id": f"row-{idx+1}", "variables": row.to_dict()})

    return profiles

  # nhớ đảm bảo đầu file có import này


class MainWindow(QMainWindow):

    def get_logger(self, profile_name):
        log_path = f"logs/{profile_name}.log"
        os.makedirs("logs", exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"[{profile_name}] 🆕 Start new log session\n")
        def logger(msg):
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{profile_name}] {msg}\n")
            self.realtime_logs[profile_name] = f"[{profile_name}] {msg}"
        return logger

    def write_log(self, profile_name, content):
        os.makedirs("logs", exist_ok=True)
        log_file = os.path.join("logs", f"{profile_name}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(content + "\n")

    def check_proxy_alive(self, raw_proxy):
        raw_proxy = raw_proxy.strip()
        if not raw_proxy:
            return True  # Không có proxy thì coi như hợp lệ

        try:
            proxy_type = "http"
            addr = raw_proxy
            match = re.match(r"^(socks5|socks4|http)://(.+)", addr)
            if match:
                proxy_type, addr = match.groups()
            parts = addr.split(":")
            if len(parts) == 4:
                ip, port, user, pwd = parts
                addr = f"{user}:{pwd}@{ip}:{port}"
            elif "@" in addr:
                userpass, ipport = addr.split("@")
                addr = f"{userpass}@{ipport}"
            full_proxy = f"{proxy_type}://{addr}"
            proxies = {"http": full_proxy, "https": full_proxy}
            r = requests.get("https://ipinfo.io/ip", proxies=proxies, timeout=5)
            return r.status_code == 200
        except:
            return False

    def style_table(self):
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #cfe3ff;
                color: black;
            }
            QTableWidget {
                gridline-color: #d0d7e2;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #e3edf7;
                padding: 3px;
                border: none;
                font-weight: bold;
            }
        """)
    
    def browse_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.excel_input.setText(file_path)
    
    def get_base_url(self, provider):
        for cfg in self.config_list:
            if cfg.get("provider") == provider:
                return cfg.get("base_url")
        return ""

    def get_window_config(self):
        try:
            width = int(self.width_input.text())
        except ValueError:
            width = 230

        try:
            height = int(self.height_input.text())
        except ValueError:
            height = 260

        try:
            scale = float(self.scale_input.text())
        except ValueError:
            scale = 0.3

        return {"width": width, "height": height, "scale": scale}

    def __init__(self):
        super().__init__()
        apply_stylesheet(self, theme='light_blue.xml', extra={'pushbutton.icon.size': '0px'})
        self.setWindowTitle("Chrome Antidetect API By @huyit32")
        self.setGeometry(100, 100, 1200, 700)
        with open('config/config.json', encoding='utf-8') as f:
            self.config_list = json.load(f)
        self.groups, self.threads, self.running_profiles = [], [], []
        self.stop_flag = threading.Event()
        self.active_threads = []
        self.profile_row_map = {}
        self.realtime_logs = {}
        self.init_ui()
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log_column_runtime)
        self.log_timer.start(500)

    def init_ui(self):
        layout = QVBoxLayout()

        # === HÀNG 1: Tất cả các control chung 1 hàng ===
        row1 = QHBoxLayout()

        self.refresh_btn = QPushButton("🔁 Refresh")
        self.refresh_btn.clicked.connect(self.load_profiles)
        row1.addWidget(self.refresh_btn)

        # Provider Combo
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("🌐 Chọn Provider")
        provider_names = [cfg.get("provider", "unknown") for cfg in self.config_list]
        self.provider_combo.addItems(provider_names)
        self.provider_combo.currentIndexChanged.connect(self.load_groups)
        row1.addWidget(self.provider_combo)

        # Group Combo
        self.group_combo = QComboBox()
        self.group_combo.addItem("🧩 Chọn Group")
        self.group_combo.currentIndexChanged.connect(self.load_profiles)
        row1.addWidget(self.group_combo)

        # JSON Tasks Combo
        self.json_combo = QComboBox()
        self.json_combo.addItem("📄 Chọn Task")
        self.load_json_files()
        row1.addWidget(self.json_combo)

        # Sort Combo
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("🔽 Chọn Sort")
        self.sort_combo.addItems(["Sort A-Z", "Sort Z-A"])
        self.sort_combo.currentIndexChanged.connect(self.load_profiles)
        row1.addWidget(self.sort_combo)

        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search profile...")
        self.search_box.setFixedWidth(160)
        self.search_box.textChanged.connect(self.load_profiles)
        row1.addWidget(self.search_box)

        # Width / Height / Scale inputs
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("Width")
        self.width_input.setFixedWidth(60)
        row1.addWidget(self.width_input)

        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("Height")
        self.height_input.setFixedWidth(60)
        row1.addWidget(self.height_input)

        self.scale_input = QLineEdit()
        self.scale_input.setPlaceholderText("Scale")
        self.scale_input.setFixedWidth(60)
        row1.addWidget(self.scale_input)

        layout.addLayout(row1)

        # === HÀNG 2: Start & Stop Buttons ===
        row2 = QHBoxLayout()
        row2.addStretch()
        self.start_btn = QPushButton("▶️ Start")
        self.start_btn.clicked.connect(self.run_selected_profiles)
        row2.addWidget(self.start_btn)

        self.stop_btn = QPushButton("🕑 Stop")
        self.stop_btn.clicked.connect(self.stop_all_threads)
        self.stop_btn.setVisible(False)
        row2.addWidget(self.stop_btn)

        layout.addLayout(row2)

        # === BẢNG ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Profile Name", "Group", "Source", "Proxy", "Log", "View"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)

        # === Overlay loading phủ toàn bảng
        self.loading_overlay = QLabel(self.table)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.setText("🔄 <b>Loading profiles...</b>")
        self.loading_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 210);  /* Phủ mờ */
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }
        """)
        self.loading_overlay.setVisible(False)

        layout.addWidget(self.table)
        self.style_table()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.load_groups()

    def update_log_column_runtime(self):
        for profile in self.running_profiles:
            name = profile['name']
            last_line = self.realtime_logs.get(name, "⏳ Đang chạy...")

            # Loại bỏ tên profile khỏi log nếu có
            prefix = f"[{name}]"
            if last_line.startswith(prefix):
                last_line = last_line[len(prefix):].strip()

            # Cập nhật log nếu có sự thay đổi
            if self.realtime_logs.get(name) != last_line:
                row = self.profile_row_map.get(name)
                if row is not None:
                    # Hiển thị log vào cột
                    item = QTableWidgetItem(last_line)

                    # Màu sắc theo trạng thái
                    if "❌" in last_line:
                        item.setForeground(Qt.red)
                    elif "✅" in last_line or "Done" in last_line:
                        item.setForeground(Qt.darkGreen)
                    elif "⚠️" in last_line:
                        item.setForeground(Qt.darkYellow)
                    elif "⏳" in last_line:
                        item.setForeground(Qt.blue)

                    # Gán log vào bảng
                    self.table.setItem(row, 4, item)

                # Lưu log mới lại để so sánh vòng sau
                self.realtime_logs[name] = last_line

    def load_json_files(self):
        self.json_combo.clear()
        self.json_combo.addItem("📄 Chọn Task")  # Placeholder
        json_files = [f for f in os.listdir("actions") if f.endswith(".json")]
        self.json_combo.addItems(json_files)

    def load_groups(self):
        provider = self.provider_combo.currentText()
        base_url = self.get_base_url(provider)
        self.groups = get_groups(provider, base_url)

        self.group_combo.clear()
        self.group_combo.addItem("🧩 Chọn Group", userData=None)  # Placeholder dòng đầu

        for group in self.groups:
            self.group_combo.addItem(group['name'], userData=group['id'])

        # Đảm bảo combo luôn hiển thị dòng placeholder đầu tiên
        self.group_combo.setCurrentIndex(0)

    def load_profiles(self):
        self.loading_overlay.resize(self.table.size())  # Phủ toàn bảng
        self.loading_overlay.move(0, 0)
        self.loading_overlay.show()
        QApplication.processEvents()

        provider = self.provider_combo.currentText()
        base_url = base_url = self.get_base_url(provider)
        group_id = self.group_combo.currentData()

        search_text = self.search_box.text().lower()

        thread = ProfileLoaderThread(provider, base_url, group_id)
        self.active_threads.append(thread)
        thread.profiles_loaded.connect(lambda profiles: self.populate_profiles(profiles, search_text))
        thread.start()

    def populate_profiles(self, profiles, search_text):
        self.loading_overlay.hide()  # Ẩn overlay sau khi load xong
        self.table.setRowCount(0)  # Xóa tất cả các dòng trong bảng trước khi thêm mới
        provider = self.provider_combo.currentText()
        self.profiles = [normalize_profile(p, provider, self.groups) for p in profiles]

        # Lọc profiles theo từ khoá tìm kiếm
        if search_text:
            profiles = [profile for profile in profiles if search_text in profile['name'].lower()]

        # Lấy giá trị sắp xếp từ dropdown
        sort_order = self.sort_combo.currentText()

        # Sắp xếp các profile A-Z hoặc Z-A
        if sort_order == "Sort A-Z":
            profiles.sort(key=lambda x: x['name'].lower())  # Sắp xếp tên theo A-Z
        elif sort_order == "Sort Z-A":
            profiles.sort(key=lambda x: x['name'].lower(), reverse=True)  # Sắp xếp tên theo Z-A

        # Điền thông tin các profile vào bảng
        for profile in profiles:
            normalized = normalize_profile(profile, provider, self.groups)

            row = self.table.rowCount()
            self.profile_row_map[normalized["name"]] = row
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(normalized["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(normalized["group_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(normalized["provider"]))
            self.table.setItem(row, 3, QTableWidgetItem(normalized["proxy"]))
            self.table.setItem(row, 4, QTableWidgetItem(""))

            btn = QPushButton("≡")
            btn.clicked.connect(lambda _, p=normalized["name"]: self.open_log(p))
            self.table.setCellWidget(row, 5, btn)


        # Dọn dẹp thread sau khi hoàn thành
        sender_thread = self.sender()
        if sender_thread in self.active_threads:
            self.active_threads.remove(sender_thread)
            sender_thread.quit()
            sender_thread.wait()
            sender_thread.deleteLater()

    def open_log(self, profile_name):
        LogDialog(profile_name).exec_()

    def move_single_window(self, profile_name, index):
        screen_w, screen_h = pyautogui.size()

        config = self.get_window_config()
        width = config["width"]
        height = config["height"]
        scale = config["scale"]

        cols = max(1, screen_w // width)
        col = index % cols
        row = index // cols
        x = col * width
        y = row * height

        for _ in range(10):
            windows = [w for w in gw.getWindowsWithTitle(profile_name) if w.visible and profile_name.lower() in w.title.lower()]
            if windows:
                try:
                    win = windows[0]
                    win.restore()
                    win.moveTo(x, y)
                    win.resizeTo(width, height)
                    return
                except Exception as e:
                    print(f"⚠️ Không thể sắp xếp cửa sổ {profile_name}: {e}")
            time.sleep(0.5)

    def handle_proxy_result(self, result):
        name = result['name']
        row = self.profile_row_map.get(name)
        proxy = result['proxy']
        valid = result['valid']
        logger = self.get_logger(name)

        if valid:
            self.running_profiles.append(next(p for p in self.profiles if p['name'] == name))
            logger(f"✅ Proxy hợp lệ: {proxy}")
            self.table.setItem(row, 4, QTableWidgetItem(f"✅ Proxy hợp lệ: {proxy}"))
        else:
            self.invalid_profiles.append(name)
            logger(f"❌ Proxy không hợp lệ: {proxy}")
            self.table.setItem(row, 4, QTableWidgetItem(f"❌ Proxy không hợp lệ: {proxy}"))

        self.checked_count += 1

        # Khi đã xử lý hết kết quả proxy → bắt đầu chạy profile
        if self.checked_count == self.total_to_check:
            if not self.running_profiles:
                self.write_log("system", "⚠️ Không có proxy hợp lệ.")
                self.start_btn.setVisible(True)
                self.stop_btn.setVisible(False)
                return
            self.start_profiles_after_check()

    def start_profiles_after_check(self):
        for idx, profile in enumerate(self.running_profiles):
            t = threading.Thread(target=self.run_profile, args=(
                self.provider, self.base_url, profile, self.selected_json, idx))
            t.start()
            self.threads.append(t)

    def run_selected_profiles(self):
        selected_json = self.json_combo.currentText()
        provider = self.provider_combo.currentText()
        base_url = self.get_base_url(provider)
        group_id = self.group_combo.currentData()

        # 1. Kiểm tra group
        if group_id is None:
            QMessageBox.warning(self, "🧩 Chưa chọn Group", "Boss ơi, mình chưa chọn Group nào hết.")
            return

        # 2. Kiểm tra file JSON
        if selected_json == "📄 Chọn Task":
            QMessageBox.warning(self, "🚫 Thiếu thông tin", "Boss ơi, mình chưa chọn file JSON để chạy rồi đó!")
            return

        # 3. Kiểm tra profile đã chọn
        selected_rows = self.table.selectionModel().selectedRows()
        selected_names = [self.table.item(r.row(), 0).text() for r in selected_rows]
        if not selected_names:
            QMessageBox.warning(self, "⚠️ Chưa chọn profile", "Boss chưa chọn profile nào để chạy.")
            return

        # 4. Reset trạng thái
        self.running_profiles = []
        self.invalid_profiles = []
        self.proxy_threads = []
        self.checked_count = 0
        self.total_to_check = len(selected_names)
        self.selected_json = selected_json
        self.provider = provider
        self.base_url = base_url
        self.stop_flag.clear()
        self.threads.clear()
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(True)

        # 5. Bắt đầu kiểm tra proxy
        for p in self.profiles:
            if p['name'] in selected_names:
                row = self.profile_row_map.get(p['name'])
                if row is not None:
                    self.table.setItem(row, 4, QTableWidgetItem("🔍 Đang kiểm tra proxy..."))

                thread = ProxyCheckThread(p, self.check_proxy_alive)
                thread.result_signal.connect(self.handle_proxy_result)
                thread.start()
                self.proxy_threads.append(thread)

    def run_profile(self, provider, base_url, profile, json_file, index):
            logger = self.get_logger(profile['name'])
            logger("⏳ Đang chạy...")

            window_config = self.get_window_config()

            profile_data = start_profile(provider, base_url, profile['id'], window_config)
            if not profile_data or not profile_data.get("debugger_address"):
                logger("❌ Không lấy được debugger_address.")
                return

            time.sleep(2)
            self.move_single_window(profile['name'], index)

            if self.stop_flag.is_set():
                logger("🚫 Dừng bởi người dùng.")
                close_profile(provider, base_url, profile['id'])
                return

            execute_blocks_from_json(
                f"actions/{json_file}",
                logger,
                profile_data.get('webdriver_path'),
                profile_data.get('debugger_address'),
                profile,
                provider, base_url, self.stop_flag
            )

            alive_threads = [t for t in self.threads if t.is_alive()]
            if not alive_threads:
                self.stop_btn.setVisible(False)
                self.start_btn.setVisible(True)

    def stop_all_threads(self):
        self.stop_flag.set()
        provider = self.provider_combo.currentText()  
        base_url = self.get_base_url(provider)        
        for profile in self.running_profiles:
            close_profile(provider, base_url, profile['id'])
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        print("🛑 All profiles were flagged to stop.")

