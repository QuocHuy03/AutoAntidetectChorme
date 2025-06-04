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
import re


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

    variables = {}
    loop_flags = []  # stack of loop control flags

    def render(text, local_vars):
        if isinstance(text, str):
            # Replace {{var}} with real value
            for key, val in local_vars.items():
                text = text.replace(f"{{{{{key}}}}}", str(val))
            return text
        return text

    def execute_block(block, local_vars):
        nonlocal variables, loop_flags
        action = block.get('action')
        xpath = render(block.get('xpath', ''), local_vars)
        value = render(block.get('value', ''), local_vars)

        try:
            if action == 'open_url':
                driver.get(value)
                logger(f"[{profile_name}] → OPEN URL - {value}")

            elif action == 'loop':
                count = int(block.get('count', 1))
                start = int(block.get('start', 0))
                var_name = block.get('variable', 'i')
                loop_blocks = block.get('do', [])
                for i in range(start, start + count):
                    variables[var_name] = i  # Cập nhật biến toàn cục
                    loop_vars = variables.copy()  # Thay vì local_vars.copy()
                    loop_flags.append({'break': False, 'continue': False})
                    for lb in loop_blocks:
                        if loop_flags[-1]['break']:
                            break
                        if loop_flags[-1]['continue']:
                            loop_flags[-1]['continue'] = False
                            break
                        execute_block(lb, loop_vars)
                    loop_flags.pop()

            elif action == 'while':
                condition = block.get('condition')
                var_name = block.get('variable', 'i')
                loop_blocks = block.get('do', [])
                while eval(condition, {}, variables):
                    loop_vars = local_vars.copy()
                    loop_vars.update(variables)
                    loop_flags.append({'break': False, 'continue': False})
                    for lb in loop_blocks:
                        if loop_flags[-1]['break']:
                            break
                        if loop_flags[-1]['continue']:
                            loop_flags[-1]['continue'] = False
                            break
                        execute_block(lb, loop_vars)
                    loop_flags.pop()

            elif action == 'break_loop':
                if loop_flags:
                    loop_flags[-1]['break'] = True

            elif action == 'next_loop':
                if loop_flags:
                    loop_flags[-1]['continue'] = True

            elif action == 'set_variable':
                variables[block['name']] = block['value']

            elif action == 'increase_variable':
                name = block['name']
                by = int(block.get('by', 1))
                variables[name] = variables.get(name, 0) + by

            elif action == 'decrease_variable':
                name = block['name']
                by = int(block.get('by', 1))
                variables[name] = variables.get(name, 0) - by

            elif action == 'input_text':
                elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                elem.clear()
                elem.send_keys(value)
                logger(f"[{profile_name}] → NHẬP => {xpath}")

            elif action == 'click':
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                logger(f"[{profile_name}] → CLICK => {xpath}")

            elif action == 'click_coords':
                x, y = map(int, value.strip().split(','))
                webdriver.ActionChains(driver).move_by_offset(x, y).click().perform()
                logger(f"[{profile_name}] 🖱️ CLICK theo tọa độ: ({x}, {y})")
                webdriver.ActionChains(driver).move_by_offset(-x, -y).perform()

            elif action == 'input_press_key':
                elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                key = getattr(Keys, value.upper(), None)
                if key:
                    elem.click()
                    elem.send_keys(key)
                    logger(f"[{profile_name}] → PRESS KEY {value.upper()} tại {xpath}")
                else:
                    logger(f"[{profile_name}] ❌ Phím không hợp lệ: {value}")

            elif action == 'element_exists':
                elements = driver.find_elements(By.XPATH, xpath)
                exists = len(elements) > 0
                logger(f"[{profile_name}] → ELEMENT {'TỒN TẠI' if exists else 'KHÔNG TỒN TẠI'} => {xpath}")
                if exists and 'if_true' in block:
                    for inner in block['if_true']:
                        execute_block(inner, local_vars)
                elif not exists and 'if_false' in block:
                    for inner in block['if_false']:
                        execute_block(inner, local_vars)
                if not exists and block.get("stop_on_fail", False):
                    logger(f"[{profile_name}] 🛑 DỪNG SCRIPT do element không tồn tại và 'stop_on_fail: true'")
                    driver.quit()
                    exit()

            elif action == 'wait':
                time.sleep(float(value))
                logger(f"[{profile_name}] 🕒 WAIT {value} giây")

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
                elif value == "random":
                    direction = random.choice([-1, 1])
                    pixels = random.randint(100, 600)
                    driver.execute_script(f"window.scrollBy(0, {direction * pixels});")
                    logger(f"[{profile_name}] 🎲 Scroll ngẫu nhiên {('↓' if direction == 1 else '↑')} {pixels}px")
                else:
                    pixels = int(value)
                    driver.execute_script(f"window.scrollBy(0, {pixels});")
                    logger(f"[{profile_name}] ↕ Scroll theo pixel: {pixels}")

            elif action == 'screenshot':
                os.makedirs('screenshots', exist_ok=True)
                path = f'screenshots/{profile_name}_{int(time.time())}.png'
                driver.save_screenshot(path)
                logger(f"[{profile_name}] 📸 Screenshot lưu tại: {path}")

            elif action == 'stop_script':
                logger(f"[{profile_name}] 🛑 SCRIPT DỪNG LẠI: {value or block.get('reason', 'Không có lý do cụ thể')}")
                driver.quit()
                exit()

            time.sleep(1)

        except Exception as e:
            logger(f"[{profile_name}] → ❌ {action} {xpath} => {e}")

    for block in blocks:
        execute_block(block, variables)

    driver.quit()
    logger(f"[{profile_name}] ✅ DONE")
