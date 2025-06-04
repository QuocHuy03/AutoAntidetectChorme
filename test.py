from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QPushButton
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pygetwindow as gw
import pyautogui
import time
import sys

class StartWin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chrome Grid Launcher")
        self.setGeometry(100, 100, 320, 250)
        self.initUI()
        self.windows = []

    def initUI(self):
        layout = QGridLayout()

        self.width_input = QLineEdit("420")
        self.height_input = QLineEdit("400")
        self.hgap_input = QLineEdit("0")
        self.vgap_input = QLineEdit("0")
        self.url_input = QLineEdit("https://www.google.com")
        self.count_input = QLineEdit("6")

        layout.addWidget(QLabel("Window Width:"), 0, 0)
        layout.addWidget(self.width_input, 0, 1)
        layout.addWidget(QLabel("Window Height:"), 1, 0)
        layout.addWidget(self.height_input, 1, 1)
        layout.addWidget(QLabel("Horizontal Gap:"), 2, 0)
        layout.addWidget(self.hgap_input, 2, 1)
        layout.addWidget(QLabel("Vertical Gap:"), 3, 0)
        layout.addWidget(self.vgap_input, 3, 1)
        layout.addWidget(QLabel("Open URL:"), 4, 0)
        layout.addWidget(self.url_input, 4, 1)
        layout.addWidget(QLabel("Chrome Count:"), 5, 0)
        layout.addWidget(self.count_input, 5, 1)

        btn_open = QPushButton("Open Chrome")
        btn_open.clicked.connect(self.open_chromes)
        layout.addWidget(btn_open, 6, 0)

        btn_arrange = QPushButton("Arrange & Zoom")
        btn_arrange.clicked.connect(self.arrange_windows)
        layout.addWidget(btn_arrange, 6, 1)

        self.setLayout(layout)

    def open_chromes(self):
        count = int(self.count_input.text())
        url = self.url_input.text()
        self.windows = []

        chrome_options = Options()
        chrome_options.add_argument("--new-window")

        for _ in range(count):
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            self.windows.append(driver)
            time.sleep(1)

    def arrange_windows(self):
        time.sleep(3)
        windows = [w for w in gw.getWindowsWithTitle(" - Google Chrome") if w.visible]

        screen_w, screen_h = pyautogui.size()
        win_w = int(self.width_input.text())
        win_h = int(self.height_input.text())
        hgap = int(self.hgap_input.text())
        vgap = int(self.vgap_input.text())
        count = len(windows)

        if count == 0:
            print("❌ Không tìm thấy cửa sổ Chrome nào để sắp xếp.")
            return

        # Tính số cột và hàng tối ưu
        cols = max(1, screen_w // (win_w + hgap))
        rows = max(1, screen_h // (win_h + vgap))

        print(f"🖥️ Screen: {screen_w}x{screen_h} → Cols: {cols}, Rows: {rows}, Count: {count}")

        for idx, win in enumerate(windows[:count]):
            col = idx % cols
            row = idx // cols
            x = col * (win_w + hgap)
            y = row * (win_h + vgap)
            try:
                win.restore()
                win.moveTo(x, y)
                win.resizeTo(win_w, win_h)

                # ✅ Kích hoạt cửa sổ & gửi Ctrl + - để zoom toàn trình duyệt
                win.activate()
                time.sleep(0.5)
                for _ in range(3):  # Zoom nhỏ 3 lần
                    pyautogui.hotkey('ctrl', '-')
                    time.sleep(0.1)

            except Exception as e:
                print(f"⚠️ Không thể sắp xếp cửa sổ {idx + 1}: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = StartWin()
    win.show()
    sys.exit(app.exec_())
