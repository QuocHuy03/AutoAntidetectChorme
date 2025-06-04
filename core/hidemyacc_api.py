import requests

API_KEY = "YOUR_API_KEY"
HEADERS = {"X-API-Key": API_KEY}

def get_profiles(base_url):
    try:
        res = requests.get(f"{base_url}/v1/browser/list", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json().get('data', [])
        else:
            print(f"[HMA get_profiles] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA get_profiles] ❌ Connection Error: {e}")
    except ValueError:
        print("[HMA get_profiles] ❌ Invalid JSON response")
    return []

def start_profile(base_url, profile_id):
    try:
        res = requests.post(
            f"{base_url}/v1/browser/start",
            headers=HEADERS,
            json={"uuid": profile_id},
            timeout=5
        )
        if res.status_code == 200:
            return res.json()
        else:
            print(f"[HMA start_profile] ⚠️ Status {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"[HMA start_profile] ❌ Connection Error: {e}")
    except ValueError:
        print("[HMA start_profile] ❌ Invalid JSON response")
    return {}

def close_profile(base_url, profile_id):
    try:
        res = requests.post(
            f"{base_url}/v1/browser/stop",
            headers=HEADERS,
            json={"uuid": profile_id},
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
