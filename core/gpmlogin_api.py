# core/gpmlogin_api.py
import requests

def get_groups(base_url):
    try:
        res = requests.get(f"{base_url}/api/v3/groups")
        if res.ok:
            return res.json().get("data", [])
    except Exception as e:
        print(f"[GPM get_groups] Error: {e}")
    return []

def get_profiles(base_url, group_id=None):
    try:
        params = {"page_size": 100}
        if group_id:
            params["group_id"] = group_id
        res = requests.get(f"{base_url}/api/v3/profiles", params=params)
        if res.ok:
            return res.json().get("data", [])
    except Exception as e:
        print(f"[GPM get_profiles] Error: {e}")
    return []

def start_profile(base_url, profile_id, win_scale=0.3, win_pos=None):
   
    try:
        params = {"win_scale": win_scale}
        if win_pos:
            params["win_pos"] = f"{win_pos[0]},{win_pos[1]}"

        res = requests.get(f"{base_url}/api/v3/profiles/start/{profile_id}", params=params)
        if res.ok:
            data = res.json().get("data", {})
            return {
                "debugger_address": data.get("remote_debugging_address"),
                "webdriver_path": data.get("driver_path")
            }
    except Exception as e:
        print(f"[GPM start_profile] Error: {e}")
    return {}


def close_profile(base_url, profile_id):
    try:
        res = requests.get(f"{base_url}/api/v3/profiles/close/{profile_id}")
        if res.ok:
            return True
    except Exception as e:
        print(f"[GPM close_profile] Error: {e}")
    return False
