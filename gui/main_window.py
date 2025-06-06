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


class MainWindow(QMainWindow):
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

        # === HÀNG 1: Cấu hình & tìm kiếm ===
        row1 = QHBoxLayout()

        self.refresh_btn = QPushButton("🔁 Refresh")
        self.refresh_btn.clicked.connect(self.load_profiles)
        row1.addWidget(self.refresh_btn)

        self.provider_combo = QComboBox()
        provider_names = [cfg.get("provider", "unknown") for cfg in self.config_list]
        self.provider_combo.addItems(provider_names)
        self.provider_combo.currentIndexChanged.connect(self.load_groups)
        row1.addWidget(QLabel("Provider:"))
        row1.addWidget(self.provider_combo)

        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.load_profiles)
        row1.addWidget(QLabel("Group:"))
        row1.addWidget(self.group_combo)

        self.json_combo = QComboBox()
        self.load_json_files()
        row1.addWidget(QLabel("Tasks:"))
        row1.addWidget(self.json_combo)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sort A-Z", "Sort Z-A"])
        self.sort_combo.currentIndexChanged.connect(self.load_profiles)
        row1.addWidget(QLabel("Sort:"))
        row1.addWidget(self.sort_combo)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["manual", "profile", "row"])
        row1.addWidget(QLabel("Excel Mode:"))
        row1.addWidget(self.mode_combo)

        self.excel_input = QLineEdit()
        self.excel_input.setPlaceholderText("File Excel (.xlsx)")
        self.excel_input.setFixedWidth(150)
        row1.addWidget(self.excel_input)

        self.select_excel_btn = QPushButton("📂")
        self.select_excel_btn.clicked.connect(self.browse_excel_file)
        row1.addWidget(self.select_excel_btn)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search...")
        self.search_box.setFixedWidth(160)
        self.search_box.textChanged.connect(self.load_profiles)
        row1.addWidget(self.search_box)

        layout.addLayout(row1)

        # === HÀNG 2: Window Config + Nút Start/Stop ===
        row2 = QHBoxLayout()

        row2.addWidget(QLabel("W:"))
        self.width_input = QLineEdit("230")
        self.width_input.setFixedWidth(50)
        row2.addWidget(self.width_input)

        row2.addWidget(QLabel("H:"))
        self.height_input = QLineEdit("260")
        self.height_input.setFixedWidth(50)
        row2.addWidget(self.height_input)

        row2.addWidget(QLabel("Scale:"))
        self.scale_input = QLineEdit("0.4")
        self.scale_input.setFixedWidth(50)
        row2.addWidget(self.scale_input)

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

        self.loading_overlay = QLabel("🔄 <b>Loading profiles...</b>", self.table)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.setStyleSheet("""
            background-color: rgba(255, 255, 255, 240);
            border: 1px solid #ccc;
            border-radius: 12px;
            font-size: 16px;
            padding: 20px;
            color: #222;
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
            log_path = f"logs/{name}.log"

            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        last_line = lines[-1].strip() if lines else "⏳ Đang chạy..."
                except Exception as e:
                    last_line = f"⚠️ Lỗi đọc log: {e}"

                # Loại bỏ tên profile khỏi log (ví dụ: "[Profile_01] ✅ DONE" -> "✅ DONE")
                prefix = f"[{name}]"
                if last_line.startswith(prefix):
                    last_line = last_line[len(prefix):].strip()

                # Cập nhật log nếu có sự thay đổi
                if self.realtime_logs.get(name) != last_line:
                    row = self.profile_row_map.get(name)
                    if row is not None:
                        # Hiển thị thông báo log vào cột
                        item = QTableWidgetItem(last_line)
                        
                        # Phân biệt màu sắc dựa trên trạng thái
                        if "❌" in last_line:
                            item.setForeground(Qt.red)
                        elif "✅" in last_line or "Done" in last_line:
                            item.setForeground(Qt.darkGreen)
                        elif "⚠️" in last_line:
                            item.setForeground(Qt.darkYellow)
                        elif "⏳" in last_line:
                            item.setForeground(Qt.blue)
                        
                        # Cập nhật vào bảng
                        self.table.setItem(row, 4, item)
                    self.realtime_logs[name] = last_line

    def load_json_files(self):
        self.json_combo.clear()
        for file in os.listdir("actions") if os.path.exists("actions") else []:
            if file.endswith(".json"):
                self.json_combo.addItem(file)

    def load_groups(self):
        provider = self.provider_combo.currentText()
        base_url = base_url = self.get_base_url(provider)
        self.groups = get_groups(provider, base_url)
        self.group_combo.clear()
        for group in self.groups:
            self.group_combo.addItem(group['name'], userData=group['id'])

    def load_profiles(self):
        self.loading_overlay.setFixedSize(300, 80)
        x = (self.table.width() - self.loading_overlay.width()) // 2
        y = (self.table.height() - self.loading_overlay.height()) // 2
        self.loading_overlay.move(x, y)
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

    def run_selected_profiles(self):
        selected_json = self.json_combo.currentText()
        provider = self.provider_combo.currentText()
        base_url = base_url = self.get_base_url(provider)
        excel_mode = self.mode_combo.currentText()
        excel_path = self.excel_input.text().strip()
        # 🔒 Bắt buộc phải chọn file Excel nếu ở chế độ 'profile'
        if excel_mode == "profile" or excel_mode == "row" and not os.path.exists(excel_path):
            QMessageBox.warning(self, "Lỗi Thiếu Excel", "Vui lòng chọn file Excel khi ở chế độ 'PROFILE'.")
            return
        
        selected_rows = self.table.selectionModel().selectedRows()
        selected_names = [self.table.item(r.row(), 0).text() for r in selected_rows]

        # ✅ Nếu đang ở mode 'profile' → lọc trùng giữa UI và Excel
        if excel_mode == "profile" and os.path.exists(excel_path):
            try:
                import pandas as pd
                df = pd.read_excel(excel_path)
                excel_names = df['PROFILE'].astype(str).str.strip().tolist()
                selected_names = [name for name in selected_names if name in excel_names]
            except Exception as e:
                QMessageBox.critical(self, "Lỗi Excel", f"Không thể đọc file Excel:\n{e}")
                return

        self.running_profiles = [p for p in self.profiles if p['name'] in selected_names]

        if not self.running_profiles:
            QMessageBox.information(self, "Thông báo", "Không có profile nào hợp lệ để chạy.")
            return

        self.stop_flag.clear()
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.threads.clear()

        for idx, profile in enumerate(self.running_profiles):
            t = threading.Thread(target=self.run_profile, args=(
                provider, base_url, profile, selected_json, idx))
            t.start()
            self.threads.append(t)

    def stop_all_threads(self):
        self.stop_flag.set()
        provider = self.provider_combo.currentText()  
        base_url = self.get_base_url(provider)        
        for profile in self.running_profiles:
            close_profile(provider, base_url, profile['id'])
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        print("🛑 All profiles were flagged to stop.")

    def run_profile(self, provider, base_url, profile, json_file, index):
        log_path = f"logs/{profile['name']}.log"
        os.makedirs("logs", exist_ok=True)

        def logger(msg):
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"[{profile['name']}] Start with {json_file}\n")

              
        window_config = self.get_window_config()
  
        profile_data = start_profile(provider, base_url, profile['id'], window_config)
        if not profile_data or not profile_data.get("debugger_address"):
            logger(f"{profile['name']} ❌ Không lấy được debugger_address.")
            return


        time.sleep(2)
        self.move_single_window(profile['name'], index)

        if self.stop_flag.is_set():
            logger(f"{profile['name']} 🚫 Dừng bởi người dùng.")
            close_profile(provider, base_url, profile['id'])
            return

        execute_blocks_from_json(
            f"actions/{json_file}",
            logger,
            profile_data.get('webdriver_path'),
            profile_data.get('debugger_address'),
            profile, provider, base_url, self.stop_flag,
            excel_mode=self.mode_combo.currentText(),
            excel_path=self.excel_input.text() if self.excel_input.text() else None
        )

        alive_threads = [t for t in self.threads if t.is_alive()]
        if not alive_threads:
            self.stop_btn.setVisible(False)
            self.start_btn.setVisible(True)
