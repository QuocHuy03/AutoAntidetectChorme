# core/action_blocks.py
import json
import time, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def execute_blocks_from_json(json_path, logger, driver_path, debugger_address, profile_name):
    with open(json_path, 'r', encoding='utf-8') as f:
        blocks = json.load(f)

    chrome_options = Options()
    chrome_options.debugger_address = debugger_address

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    for block in blocks:
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
                logger(f"[{profile_name}] → NHẬP => {xpath} - Executing BrowserKeyPress")
            elif action == 'click':
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
                logger(f"[{profile_name}] → CLICK => {xpath}")
            time.sleep(1)
        except Exception as e:
            logger(f"[{profile_name}] → ❌ {action} {xpath} => {e}")

    driver.quit()
    logger(f"[{profile_name}] ✅ DONE")
