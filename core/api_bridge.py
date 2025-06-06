from core.gpmlogin_api import get_groups as gpm_get_groups, get_profiles as gpm_get_profiles, start_profile as gpm_start_profile, close_profile as gpm_close_profile
from core.hidemyacc_api import get_groups as hma_get_groups, get_profiles as hma_get_profiles, start_profile as hma_start_profile, close_profile as hma_close_profile


def get_groups(provider, base_url):
    if provider == "gpmlogin":
        return gpm_get_groups(base_url)
    if provider == "hidemyacc":
        return hma_get_groups(base_url)
    return []


def get_profiles(provider, base_url, group_id=None):
    print(f"[API_BRIDGE] get_profiles → provider: {provider}, base_url: {base_url}, group_id: {group_id}")
    if provider == "gpmlogin":
        return gpm_get_profiles(base_url, group_id)
    if provider == "hidemyacc":
        return hma_get_profiles(base_url, group_id)
    return []


def start_profile(provider, base_url, profile_id, window_config):
    if provider == 'gpmlogin':
        return gpm_start_profile(base_url, profile_id, window_config)
    if provider == "hidemyacc":
        return hma_start_profile(base_url, profile_id, window_config)
    return {}

def close_profile(provider, base_url, profile_id):
    if provider == "gpmlogin":
        return gpm_close_profile(base_url, profile_id)
    if provider == "hidemyacc":
        return hma_close_profile(base_url, profile_id)
    return {}



def normalize_profile(profile, provider, groups=None):
    """
    Chuẩn hóa profile từ nhiều nguồn API khác nhau về 1 định dạng duy nhất.
    Dễ bảo trì, mở rộng nhiều provider chỉ bằng cách sửa dict MAPPINGS.
    """

    MAPPINGS = {
        "id": ["id", "uuid", "profile_id"],
        "name": ["name", "profile_name", "title", "label"],
        "group_id": ["group_id", "folder_id", "folder"],
        "proxy": ["raw_proxy", "proxy", "proxy_url"]
    }

    def extract(field):
        for key in MAPPINGS.get(field, []):
            value = profile.get(key)
            if value:
                return value
        return ""

    name = extract("name") or "Unknown"
    profile_id = extract("id")
    group_id = extract("group_id")
    raw_proxy = extract("proxy")

    # Nếu là dict (HMA), chuyển về chuỗi IP:PORT
    if isinstance(raw_proxy, dict):
        host = raw_proxy.get("host", "")
        port = str(raw_proxy.get("port", ""))
        proxy = f"{host}:{port}" if host else ""
    else:
        proxy = str(raw_proxy)

    # Xử lý tên nhóm
    group_name = str(group_id)
    if groups:
        for g in groups:
            if g.get("id") == group_id:
                group_name = g.get("name", group_name)
                break

    return {
        "id": profile_id,
        "name": name,
        "group_name": group_name,
        "provider": provider,
        "proxy": proxy,
        "original": profile
    }
