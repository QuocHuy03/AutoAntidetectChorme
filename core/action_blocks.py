import json
import time, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import random


def execute_blocks_from_json(json_path, logger, driver_path, debugger_address, profile_name):
    with open(json_path, 'r', encoding='utf-8') as f:
        blocks = json.load(f)

    chrome_options = Options()
    if isinstance(debugger_address, str):
        chrome_options.debugger_address = debugger_address
    else:
        raise ValueError(f"⚠️ debugger_address không hợp lệ: {debugger_address}")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    def execute_block(block):
        action = block.get('action')
        xpath = block.get('xpath', '')
        value = block.get('value', '')

        try:
            if action == 'open_url':
                driver.get(value)
                logger(f"[{profile_name}] → OPEN URL - {value}")

            elif action == 'input_text':
                elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.clear()
                elem.send_keys(value)
                logger(f"[{profile_name}] → NHẬP => {xpath}")

            elif action == 'click':
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                logger(f"[{profile_name}] → CLICK => {xpath}")
            
            elif action == 'click_coords':
                try:
                    x, y = map(int, value.strip().split(','))
                    webdriver.ActionChains(driver).move_by_offset(x, y).click().perform()
                    logger(f"[{profile_name}] 🖱️ CLICK theo tọa độ: ({x}, {y})")
                    webdriver.ActionChains(driver).move_by_offset(-x, -y).perform()  # Reset lại offset
                except Exception as e:
                    logger(f"[{profile_name}] ❌ CLICK theo tọa độ thất bại: {value} => {e}")

            elif action == 'input_press_key':
                elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                key = getattr(Keys, value.upper(), None)
                if key:
                    try:
                        elem.click()  # 👉 Đảm bảo focus vào element
                        elem.send_keys(key)
                        logger(f"[{profile_name}] → PRESS KEY {value.upper()} tại {xpath}")
                    except Exception as e:
                        logger(f"[{profile_name}] ❌ Không gửi được key {value.upper()} tại {xpath}: {e}")
                else:
                    logger(f"[{profile_name}] ❌ Phím không hợp lệ: {value}")

            elif action == 'element_exists':
                elements = driver.find_elements(By.XPATH, xpath)
                exists = len(elements) > 0
                logger(f"[{profile_name}] → ELEMENT {'TỒN TẠI' if exists else 'KHÔNG TỒN TẠI'} => {xpath}")

                if exists and 'if_true' in block:
                    for inner_block in block['if_true']:
                        execute_block(inner_block)
                elif not exists and 'if_false' in block:
                    for inner_block in block['if_false']:
                        execute_block(inner_block)

                if not exists and block.get("stop_on_fail", False):
                    logger(f"[{profile_name}] 🛑 DỪNG SCRIPT do element không tồn tại và 'stop_on_fail: true'")
                    driver.quit()
                    exit()

            elif action == 'wait':
                delay = float(value)
                time.sleep(delay)
                logger(f"[{profile_name}] 🕒 WAIT {delay} giây")

            elif action == 'scroll':
                if value == "down":
                    driver.execute_script("window.scrollBy(0, 300);")
                    logger(f"[{profile_name}] ↓ Scroll xuống 300px")
                elif value == "up":
                    driver.execute_script("window.scrollBy(0, -300);")
                    logger(f"[{profile_name}] ↑ Scroll lên 300px")
                elif value == "to_bottom":
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    logger(f"[{profile_name}] ↓ Scroll xuống cuối trang")
                elif value == "to_top":
                    driver.execute_script("window.scrollTo(0, 0);")
                    logger(f"[{profile_name}] ↑ Scroll lên đầu trang")
                elif value == "element":
                    if xpath:
                        elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                        logger(f"[{profile_name}] 🔍 Scroll tới element: {xpath}")
                    else:
                        logger(f"[{profile_name}] ❌ scroll: cần chỉ định 'xpath' khi dùng value='element'")
                elif value == "random":
                    direction = random.choice([-1, 1])  # -1 = scroll up, 1 = scroll down
                    pixels = random.randint(100, 600)
                    driver.execute_script(f"window.scrollBy(0, {direction * pixels});")
                    logger(f"[{profile_name}] 🎲 Scroll ngẫu nhiên {('↓' if direction == 1 else '↑')} {pixels}px")
                else:
                    try:
                        pixels = int(value)
                        driver.execute_script(f"window.scrollBy(0, {pixels});")
                        logger(f"[{profile_name}] ↕ Scroll theo pixel: {pixels}")
                    except ValueError:
                        logger(f"[{profile_name}] ❌ scroll: Giá trị '{value}' không hợp lệ")
            
            elif action == 'screenshot':
                os.makedirs('screenshots', exist_ok=True)
                path = f'screenshots/{profile_name}_{int(time.time())}.png'
                driver.save_screenshot(path)
                logger(f"[{profile_name}] 📸 Screenshot lưu tại: {path}")

            time.sleep(1)

        except Exception as e:
            logger(f"[{profile_name}] → ❌ {action} {xpath} => {e}")

    # Run each block
    for block in blocks:
        execute_block(block)

    driver.quit()
    logger(f"[{profile_name}] ✅ DONE")
