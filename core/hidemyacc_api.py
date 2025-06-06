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
            "additional_args": additional_args
        }
        res = requests.post(
            f"{base_url}/profiles/start/{profile_id}",
            json=json_data,
            timeout=5
        )
        if res.status_code == 200:
            data = res.json().get("data", {})
            return {
                "debugger_address": data.get("wsUrl"),
                "webdriver_path": "chromedriver"
            }
        else:
            print(f"[HMA start_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA start_profile] ❌ Connection Error: {e}")
    except ValueError:
        print(f"[HMA start_profile] ❌ Invalid JSON response")
    return {}

def close_profile(base_url, profile_id):
    try:
        res = requests.post(
            f"{base_url}/profiles/stop/{profile_id}",
            timeout=5
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
