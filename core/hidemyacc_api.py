import requests

def get_groups(base_url):
    try:
        res = requests.get(f"{base_url}/folders", timeout=5)
        if res.status_code == 200:
            return res.json().get("data", [])
        else:
            print(f"[HMA get_groups] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA get_groups] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[HMA get_groups] ❌ Invalid JSON response")
    return []

def get_profiles(base_url, group_id=None):
    try:
        params = {}
        if group_id:
            params["folder"] = group_id
        url = f"{base_url}/profiles"
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            return res.json().get('data', [])
        else:
            print(f"[HMA get_profiles] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA get_profiles] ❌ Connection Error: {e}")
    except ValueError:
        print("[HMA get_profiles] ❌ Invalid JSON response")
    return []

def start_profile(base_url, profile_id, window_config):
    try:
        additional_args = f"--disable-gpu --window-size={window_config['width']},{window_config['height']} --force-device-scale-factor={window_config['scale']}"
        json_data = {
            "params": additional_args
        }
        res = requests.post(
            f"{base_url}/profiles/start/{profile_id}",
            json=json_data,
            timeout=20
        )
        if res.status_code == 200:
            data = res.json().get("data", {})
            print("HMA", data)
            return {
                "debugger_address": f"127.0.0.1:{data.get("port")}",
                "webdriver_path": "chromedriver.exe"
            }
        else:
            print(f"[HMA start_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA start_profile] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[HMA start_profile] ❌ Invalid JSON response")
    return {}

def update_profile(base_url, profile_id, data_update):
    try:
        # Đảm bảo có trường name, nếu không có thì báo lỗi
        name = data_update.get("name") or data_update.get("profile_name")
        if not name:
            print(f"[HMA update_profile] ❌ Thiếu 'name' trong data_update")
            return False

        update_data = {
            "profile_name": name,
            "majorVersion": "135.0.0.0"
        }

        res = requests.put(
            f"{base_url}/profiles/{profile_id}",
            json=update_data,
            timeout=10
        )

        if res.status_code == 200:
            print(f"[{name}] ✅ Đã ép về Chrome 135 thành công.")
            return True
        else:
            print(f"[{name}] ❌ Lỗi update: {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA update_profile] ❌ Connection Error: {e}")
    except Exception as e:
        print(f"[HMA update_profile] ❌ Unknown error: {e}")
    return False

def close_profile(base_url, profile_id):
    try:
        res = requests.post(
            f"{base_url}/profiles/stop/{profile_id}",
            timeout=20
        )
        if res.status_code == 200:
            return res.json()
        else:
            print(f"[HMA close_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA close_profile] ❌ Connection Error: {e}")
    except ValueError:
        print("[HMA close_profile] ❌ Invalid JSON response")
    return {}
