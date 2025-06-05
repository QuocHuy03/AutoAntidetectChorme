from core.gpmlogin_api import get_groups as gpm_get_groups, get_profiles as gpm_get_profiles, start_profile as gpm_start_profile, close_profile as gpm_close_profile
from core.hidemyacc_api import get_profiles as hma_get_profiles, start_profile as hma_start_profile, close_profile as hma_close_profile


def get_groups(provider, base_url):
    if provider == "gpmlogin":
        return gpm_get_groups(base_url)
    return []

def get_profiles(provider, base_url, group_id=None):
    print(f"[API_BRIDGE] get_profiles → provider: {provider}, base_url: {base_url}, group_id: {group_id}")
    if provider == "gpmlogin":
        return gpm_get_profiles(base_url, group_id)
    if provider == "hidemyacc":
        return hma_get_profiles(base_url)
    return []


def start_profile(provider, base_url, profile_id, win_scale=0.3, win_pos=None):
    if provider == 'gpmlogin':
        return gpm_start_profile(base_url, profile_id, win_scale, win_pos)
    if provider == "hidemyacc":
        return hma_start_profile(base_url, profile_id)
    return {}

def close_profile(provider, base_url, profile_id):
    if provider == "gpmlogin":
        return gpm_close_profile(base_url, profile_id)
    if provider == "hidemyacc":
        return hma_close_profile(base_url, profile_id)
    return {}