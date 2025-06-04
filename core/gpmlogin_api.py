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
    try:
        params = {"page_size": 100}
        if group_id:
            params["group_id"] = group_id
        res = requests.get(f"{base_url}/api/v3/profiles", params=params, timeout=5)
        if res.status_code == 200:
            return res.json().get("data", [])
        else:
            print(f"[GPM get_profiles] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GPM get_profiles] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[GPM get_profiles] ❌ Invalid JSON response")
    return []

def start_profile(base_url, profile_id, win_scale=0.3, win_pos=None):
    try:
        params = {"win_scale": win_scale}
        if win_pos:
            params["win_pos"] = f"{win_pos[0]},{win_pos[1]}"
        res = requests.get(f"{base_url}/api/v3/profiles/start/{profile_id}", params=params, timeout=5)
        if res.status_code == 200:
            data = res.json().get("data", {})
            return {
                "debugger_address": data.get("remote_debugging_address"),
                "webdriver_path": data.get("driver_path")
            }
        else:
            print(f"[GPM start_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[GPM start_profile] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[GPM start_profile] ❌ Invalid JSON response")
    return {}

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
