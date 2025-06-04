from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QComboBox, QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QTextEdit, QMessageBox, QApplication
)
from core.api_bridge import get_profiles, get_groups, start_profile, close_profile
from core.action_blocks import execute_blocks_from_json
import json, os, threading, time
import pygetwindow as gw
import pyautogui

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPMLogin Profile Launcher")
        self.setGeometry(100, 100, 1200, 700)
        with open('config/config.json') as f:
            self.config = json.load(f)
        self.groups, self.threads, self.running_profiles = [], [], []
        self.stop_flag = threading.Event()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        top_bar = QHBoxLayout()

        self.refresh_btn = QPushButton("🔁 Refresh")
        self.refresh_btn.clicked.connect(self.load_profiles)
        top_bar.addWidget(self.refresh_btn)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["gpmlogin", "hidemyacc"])
        self.provider_combo.currentIndexChanged.connect(self.load_groups)
        top_bar.addWidget(QLabel("Profile Type"))
        top_bar.addWidget(self.provider_combo)

        self.group_combo = QComboBox()
        self.group_combo.currentIndexChanged.connect(self.load_profiles)
        top_bar.addWidget(QLabel("Group"))
        top_bar.addWidget(self.group_combo)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search profile name...")
        self.search_box.textChanged.connect(self.load_profiles)
        top_bar.addWidget(self.search_box)

        self.json_combo = QComboBox()
        self.load_json_files()
        top_bar.addWidget(QLabel("Tasks"))
        top_bar.addWidget(self.json_combo)

        self.start_btn = QPushButton("▶️ Start")
        self.start_btn.clicked.connect(self.run_selected_profiles)
        top_bar.addWidget(self.start_btn)

        self.stop_btn = QPushButton("🕑 Stop")
        self.stop_btn.clicked.connect(self.stop_all_threads)
        self.stop_btn.setVisible(False)
        top_bar.addWidget(self.stop_btn)

        layout.addLayout(top_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Profile Name", "Group", "Source", "Log"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.load_groups()

    def load_json_files(self):
        self.json_combo.clear()
        for file in os.listdir("actions") if os.path.exists("actions") else []:
            if file.endswith(".json"):
                self.json_combo.addItem(file)

    def load_groups(self):
        provider = self.provider_combo.currentText()
        base_url = self.config['base_url']
        self.groups = get_groups(provider, base_url)
        self.group_combo.clear()
        for group in self.groups:
            self.group_combo.addItem(group['name'], userData=group['id'])
        self.load_profiles()

    def load_profiles(self):
        self.table.setRowCount(0)
        provider = self.provider_combo.currentText()
        base_url = self.config['base_url']
        group_id = self.group_combo.currentData()
        keyword = self.search_box.text().lower()
        self.profiles = get_profiles(provider, base_url, group_id)

        for profile in self.profiles:
            if keyword and keyword not in profile['name'].lower(): continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(profile['name']))
            group_name = next((g['name'] for g in self.groups if g['id'] == profile.get('group_id')), str(profile.get('group_id')))
            self.table.setItem(row, 1, QTableWidgetItem(group_name))
            self.table.setItem(row, 2, QTableWidgetItem(provider))
            btn = QPushButton("≡")
            btn.clicked.connect(lambda _, p=profile['name']: self.open_log(p))
            self.table.setCellWidget(row, 3, btn)

    def open_log(self, profile_name):
        LogDialog(profile_name).exec_()

    def stop_all_threads(self):
        self.stop_flag.set()
        base_url = self.config['base_url']
        provider = self.provider_combo.currentText()
        for profile in self.running_profiles:
            close_profile(provider, base_url, profile['id'])
        self.stop_btn.setVisible(False)

    def move_single_window(self, profile_name, index):
        screen_w, screen_h = pyautogui.size()
        win_w, win_h = 220, 200
        hgap, vgap = 0, 0
        cols = max(1, screen_w // (win_w + hgap))
        col = index % cols
        row = index // cols
        x = col * (win_w + hgap)
        y = row * (win_h + vgap)
        print(f"[Screen] {screen_w}x{screen_h} → Cols: {cols}, Count: {index}")

        for _ in range(10):
            windows = [w for w in gw.getWindowsWithTitle(profile_name) if w.visible and profile_name.lower() in w.title.lower()]
            if windows:
                try:
                    win = windows[0]
                    win.restore()
                    win.moveTo(x, y)
                    win.resizeTo(win_w, win_h)
                    return
                except Exception as e:
                    print(f"⚠️ Không thể sắp xếp cửa sổ {profile_name}: {e}")
            time.sleep(0.5)

    def run_selected_profiles(self):
        selected_json = self.json_combo.currentText()
        provider = self.provider_combo.currentText()
        base_url = self.config['base_url']
        selected_rows = self.table.selectionModel().selectedRows()
        selected_names = [self.table.item(r.row(), 0).text() for r in selected_rows]
        self.running_profiles = [p for p in self.profiles if p['name'] in selected_names]

        self.stop_flag.clear()
        self.stop_btn.setVisible(True)
        self.threads.clear()

        for idx, profile in enumerate(self.running_profiles):
            t = threading.Thread(target=self.run_profile, args=(provider, base_url, profile, selected_json, idx, len(self.running_profiles)))
            t.start()
            self.threads.append(t)

    def run_profile(self, provider, base_url, profile, json_file, index, total):
        log_path = f"logs/{profile['name']}.log"
        os.makedirs("logs", exist_ok=True)

        def logger(msg):
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"[{profile['name']}] Start with {json_file}\n")

        profile_data = start_profile(provider, base_url, profile['id'])
        time.sleep(2)

        self.move_single_window(profile['name'], index)

        if self.stop_flag.is_set():
            logger(f"{profile['name']} 🚑 Bị huỷ.")
            close_profile(provider, base_url, profile['id'])
            return

        execute_blocks_from_json(f"actions/{json_file}", logger,
                                 profile_data.get('webdriver_path'),
                                 profile_data.get('debugger_address'),
                                 profile['name'])

        if not any(t.is_alive() for t in self.threads):
            self.stop_btn.setVisible(False)
