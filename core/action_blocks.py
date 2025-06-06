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
import pandas as pd
from core.api_bridge import close_profile

def load_excel_data(excel_path: str, mode: str):
    df = pd.read_excel(excel_path)
    result = []

    if mode == "profile":
        for idx, row in df.iterrows():
            if pd.notna(row.get("PROFILE")):
                result.append({
                    "profile": {"name": row["PROFILE"]},
                    "variables": row.to_dict()
                })

    elif mode == "row":
        for idx, row in df.iterrows():
            result.append({
                "profile": {"name": f"Row-{idx+1}"},
                "variables": {"row_data": row.to_dict()}
            })

    elif mode == "manual":
        result.append({
            "profile": {"name": "manual"},
            "variables": {}
        })

    return result


def render(text, local_vars):
    if not isinstance(text, str):
        return text

    combined_vars = {}
    if "row_data" in local_vars:
        combined_vars.update(local_vars["row_data"])
    else:
        combined_vars.update(local_vars)

    for key, val in combined_vars.items():
        if pd.notna(val):
            text = text.replace(f"{{{{{key}}}}}", str(val))

    return text


def execute_blocks_from_json(json_path, logger, driver_path, debugger_address, profile_input, provider, base_url, stop_flag,
                             excel_mode='manual', excel_path=None):

    with open(json_path, 'r', encoding='utf-8') as f:
        blocks = json.load(f)

    profile = profile_input
    variables = {}

    if excel_mode == 'profile' and excel_path:
        try:
            df = pd.read_excel(excel_path)
            matched_rows = df[df['PROFILE'].astype(str).str.strip() == profile['name']]
            if matched_rows.empty:
                logger(f"[{profile['name']}] ⚠️ Bỏ qua vì không trùng với Excel.")
                return
            variables = matched_rows.iloc[0].to_dict()
        except Exception as e:
            logger(f"[{profile['name']}] ⚠️ Lỗi đọc Excel (mode=profile): {e}")
            return

    elif excel_mode == 'row' and excel_path:
        try:
            df = pd.read_excel(excel_path)
            index = int(profile['name'].replace("Row-", "")) - 1
            if 0 <= index < len(df):
                row_data = df.iloc[index]
                if row_data.dropna(how='all').empty:
                    logger(f"[{profile['name']}] ⚠️ Dòng {index + 1} không có dữ liệu. Bỏ qua.")
                    return
                variables = {"row_data": row_data.to_dict()}
            else:
                logger(f"[{profile['name']}] ⚠️ Dòng {index + 1} vượt quá số dòng của Excel.")
                return
        except Exception as e:
            logger(f"[{profile['name']}] ⚠️ Lỗi đọc Excel (mode=row): {e}")
            return

    try:
        chrome_options = Options()
        if isinstance(debugger_address, str):
            chrome_options.debugger_address = debugger_address
        else:
            raise ValueError(f"⚠️ debugger_address không hợp lệ: {debugger_address}")

        driver_dir = os.path.abspath("chromedriver")
        driver_path = os.path.join(driver_dir, "chromedriver.exe")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        logger(f"[{profile['name']}] ❌ Không mở được trình duyệt: {e}")
        return

    loop_flags = []
    print(f"[{profile['name']}] 📥 VARS: {variables}")

    def execute_block(block, local_vars):
        nonlocal variables, loop_flags
        action = block.get('action')
        xpath = render(block.get('xpath', ''), local_vars)
        value = render(block.get('value', ''), local_vars)
        try:
                if action == 'open_url':
                    driver.get(value)
                    logger(f"[{profile['name']}] → OPEN URL - {value}")

                elif action == 'switch_tab_by_index':
                        tab_index = int(value)
                        tabs = driver.window_handles
                        if 0 <= tab_index < len(tabs):
                            driver.switch_to.window(tabs[tab_index])
                            logger(f"[{profile['name']}] 🔄 Chuyển sang tab {tab_index + 1}")
                        else:
                            logger(f"[{profile['name']}] ❌ Tab chỉ số {tab_index} không hợp lệ")

                elif action == 'switch_tab_next':
                        tabs = driver.window_handles
                        current_tab = driver.current_window_handle
                        current_index = tabs.index(current_tab)
                        next_index = (current_index + 1) % len(tabs)
                        driver.switch_to.window(tabs[next_index])
                        logger(f"[{profile['name']}] 🔄 Chuyển sang tab tiếp theo")

                elif action == 'switch_tab_prev':
                        tabs = driver.window_handles
                        current_tab = driver.current_window_handle
                        current_index = tabs.index(current_tab)
                        prev_index = (current_index - 1) % len(tabs)  # Lùi lại một tab
                        driver.switch_to.window(tabs[prev_index])
                        logger(f"[{profile['name']}] 🔄 Chuyển sang tab trước đó")

                elif action == 'navigate_back':
                    driver.back()
                    logger(f"[{profile['name']}] ⬅️ Quay lại trang trước")
                
                elif action == 'navigate_forward':
                    driver.forward()
                    logger(f"[{profile['name']}] ➡️ Tiến tới trang tiếp theo")
                
                elif action == 'refresh_page':
                    driver.refresh()
                    logger(f"[{profile['name']}] 🔄 Tải lại trang")

                elif action == 'active_tab':
                    driver.switch_to.window(driver.current_window_handle)
                    logger(f"[{profile['name']}] 🔄 Kích hoạt tab hiện tại")

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
                    logger(f"[{profile['name']}] → NHẬP => {xpath} | VALUE = {value}")

                elif action == 'click':
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                    logger(f"[{profile['name']}] → CLICK => {xpath}")

                elif action == 'click_coords':
                    x, y = map(int, value.strip().split(','))
                    webdriver.ActionChains(driver).move_by_offset(x, y).click().perform()
                    logger(f"[{profile['name']}] 🖱️ CLICK theo tọa độ: ({x}, {y})")
                    webdriver.ActionChains(driver).move_by_offset(-x, -y).perform()

                elif action == 'input_press_key':
                    elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    key = getattr(Keys, value.upper(), None)
                    if key:
                        elem.click()
                        elem.send_keys(key)
                        logger(f"[{profile['name']}] → PRESS KEY {value.upper()} tại {xpath}")
                    else:
                        logger(f"[{profile['name']}] ❌ Phím không hợp lệ: {value}")

                elif action == 'element_exists':
                    elements = driver.find_elements(By.XPATH, xpath)
                    exists = len(elements) > 0
                    logger(f"[{profile['name']}] → ELEMENT {'TỒN TẠI' if exists else 'KHÔNG TỒN TẠI'} => {xpath}")
                    
                    # Nếu phần tử tồn tại, thực hiện các hành động trong if_true
                    if exists and 'if_true' in block:
                        for inner in block['if_true']:
                            execute_block(inner, local_vars)
                    
                    # Nếu phần tử không tồn tại, thực hiện các hành động trong if_false
                    elif not exists and 'if_false' in block:
                        for inner in block['if_false']:
                            execute_block(inner, local_vars)
                    
                    # Nếu phần tử không tồn tại và stop_on_fail = true, dừng script
                    if not exists and block.get("stop_on_fail", False):
                        logger(f"[{profile['name']}] 🛑 DỪNG SCRIPT do element không tồn tại và 'stop_on_fail: true'")
                        
                        # Gọi API để đóng profile
                        close_profile(provider, base_url, profile['id'])  # Đóng profile thông qua API
                        
                        # Đảm bảo đóng trình duyệt và thoát khỏi script
                        try:
                            driver.quit()  # Đóng trình duyệt
                        except Exception as e:
                            logger(f"❌ Lỗi khi đóng trình duyệt: {e}")
                        
                        exit()  # Dừng script hoàn toàn
                
                elif action == 'upload_file':
                    file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    file_input.send_keys(value)
                    logger(f"[{profile['name']}] 📤 Đã tải lên file: {value}")

                elif action == 'wait':
                    time.sleep(float(value))
                    logger(f"[{profile['name']}] 🕒 WAIT {value} giây")

                elif action == 'switch_iframe':
                    iframe_elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                    driver.switch_to.frame(iframe_elem)
                    logger(f"[{profile['name']}] 🔄 Chuyển vào iframe với xpath: {xpath}")

                elif action == 'switch_to_default_content':
                    driver.switch_to.default_content()
                    logger(f"[{profile['name']}] 🔄 Quay lại nội dung chính của trang")
                
                elif action == 'switch_popup_window':
                    popup_window = driver.window_handles[-1]  # Chọn cửa sổ popup cuối cùng trong danh sách
                    driver.switch_to.window(popup_window)
                    logger(f"[{profile['name']}] 🔄 Chuyển sang cửa sổ popup")

                elif action == 'close_popup_window':
                    driver.close()  # Đóng cửa sổ popup hiện tại
                    driver.switch_to.window(driver.window_handles[0])  # Quay lại cửa sổ chính
                    logger(f"[{profile['name']}] 🔒 Đã đóng cửa sổ popup")
                    
                elif action == 'scroll':
                    if value == "down":
                        driver.execute_script("window.scrollBy(0, 300);")
                        logger(f"[{profile['name']}] ↓ Scroll xuống 300px")
                    elif value == "up":
                        driver.execute_script("window.scrollBy(0, -300);")
                        logger(f"[{profile['name']}] ↑ Scroll lên 300px")
                    elif value == "to_bottom":
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        logger(f"[{profile['name']}] ↓ Scroll xuống cuối trang")
                    elif value == "to_top":
                        driver.execute_script("window.scrollTo(0, 0);")
                        logger(f"[{profile['name']}] ↑ Scroll lên đầu trang")
                    elif value == "element":
                        if xpath:
                            elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                            logger(f"[{profile['name']}] 🔍 Scroll tới element: {xpath}")
                    elif value == "random":
                        direction = random.choice([-1, 1])
                        pixels = random.randint(100, 600)
                        driver.execute_script(f"window.scrollBy(0, {direction * pixels});")
                        logger(f"[{profile['name']}] 🎲 Scroll ngẫu nhiên {('↓' if direction == 1 else '↑')} {pixels}px")
                    else:
                        pixels = int(value)
                        driver.execute_script(f"window.scrollBy(0, {pixels});")
                        logger(f"[{profile['name']}] ↕ Scroll theo pixel: {pixels}")

                elif action == 'screenshot':
                    os.makedirs('screenshots', exist_ok=True)
                    path = f'screenshots/{profile['name']}_{int(time.time())}.png'
                    driver.save_screenshot(path)
                    logger(f"[{profile['name']}] 📸 Screenshot lưu tại: {path}")
                
                elif action == 'eval_script':
                    try:
                        result = driver.execute_script(value)
                        if 'store_as' in block:
                            var_name = block['store_as']
                            variables[var_name] = result
                            logger(f"[{profile['name']}] 🧠 JS Eval → Lưu '{var_name}' = {result}")
                        else:
                            logger(f"[{profile['name']}] 🧠 JS Eval → {result}")
                    except Exception as e:
                        logger(f"[{profile['name']}] ❌ eval_script lỗi: {e}")

                elif action == 'stop_script':
                    logger(f"[{profile['name']}] 🛑 SCRIPT DỪNG LẠI: {value or block.get('reason', 'Không có lý do cụ thể')}")
                    close_profile(provider, base_url, profile['id'])
                    driver.quit()
                    exit()

                time.sleep(1)

        except Exception as e:
                logger(f"[{profile['name']}] → ❌ {action} {xpath} => {e}")

    for block in blocks:
            if stop_flag.is_set():
                logger(f"[{profile['name']}] ⛔ Đã nhấn STOP – dừng script ngay lập tức.")
                if 'id' in profile:
                    close_profile(provider, base_url, profile['id'])
                try:
                    driver.quit()
                except Exception as e:
                    logger(f"[{profile['name']}] ⚠️ Lỗi khi đóng trình duyệt: {e}")
                return
            execute_block(block, variables)