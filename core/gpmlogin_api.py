import requests

def get_groups(base_url):
    try:
        res = requests.get(f"{base_url}/api/v3/groups", timeout=5)
        if res.status_code == 200:
            return res.json().get("data", [])
        else:
            print(f"[GPM get_groups] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GPM get_groups] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[GPM get_groups] ❌ Invalid JSON response")
    return []

def get_profiles(base_url, group_id=None):
    all_profiles = []
    page = 1
    try:
        while True:
            params = {"page": page, "page_size": 500}
            if group_id:
                params["group_id"] = group_id
            url = f"{base_url}/api/v3/profiles"
            res = requests.get(url, params=params, timeout=5)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if not data:
                    break
                all_profiles.extend(data)
                page += 1
            else:
                print(f"[GPM_API] ⚠️ Status {res.status_code} - {res.text}")
                break
    except Exception as e:
        print(f"[GPM_API] ❌ Exception: {e}")
    return all_profiles

def start_profile(base_url, profile_id, window_config):
    print(window_config)
    try:
        additional_args = f"--disable-gpu --window-size={window_config['width']},{window_config['height']} --force-device-scale-factor={window_config['scale']} --lang=en"
        params = {
            "addination_args": additional_args
        }
        res = requests.get(f"{base_url}/api/v3/profiles/start/{profile_id}", params=params, timeout=5)
        if res.status_code == 200:
            data = res.json().get("data", {})
            return {
                "debugger_address": data.get("remote_debugging_address"),
                "webdriver_path": 'chromedriver.exe'
            }
        else:
            print(f"[GPM start_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GPM start_profile] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[GPM start_profile] ❌ Invalid JSON response")
    return {}

def update_profile(base_url, profile_id, data_update):
    try:
        # Đảm bảo có trường name, nếu không có thì báo lỗi
        name = data_update.get("name") or data_update.get("profile_name")
        if not name:
            print(f"[GPM update_profile] ❌ Thiếu 'name' trong data_update")
            return False

        update_data = {
            "profile_name": name,
            "chromiumVersion": "135.0.0.0"
        }

        res = requests.post(
            f"{base_url}/api/v3/profiles/update/{profile_id}",
            json=update_data,
            timeout=5
        )

        if res.status_code == 200:
            print(f"[{name}] ✅ Đã ép về Chrome 129 thành công.")
            return True
        else:
            print(f"[{name}] ❌ Lỗi update: {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GPM update_profile] ❌ Connection Error: {e}")
    except Exception as e:
        print(f"[GPM update_profile] ❌ Unknown error: {e}")
    return False

def close_profile(base_url, profile_id):
    try:
        res = requests.get(f"{base_url}/api/v3/profiles/close/{profile_id}", timeout=5)
        if res.status_code == 200:
            return True
        else:
            print(f"[GPM close_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GPM close_profile] ❌ Connection Error: {e}")
    return False
