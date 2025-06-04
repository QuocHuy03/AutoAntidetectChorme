import requests

def get_profiles(base_url):
    headers = {"X-API-Key": "YOUR_API_KEY"}
    res = requests.get(f"{base_url}/v1/browser/list", headers=headers)
    return res.json().get('data', [])

def start_profile(base_url, profile_id):
    headers = {"X-API-Key": "YOUR_API_KEY"}
    requests.post(f"{base_url}/v1/browser/start", headers=headers, json={"uuid": profile_id})

def close_profile(base_url, profile_id):
    headers = {"X-API-Key": "YOUR_API_KEY"}
    requests.post(f"{base_url}/v1/browser/start", headers=headers, json={"uuid": profile_id})
