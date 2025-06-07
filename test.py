import requests

proxies = {
    "http": "http://sundayokwu12345:c2Vw96fzFP@216.180.253.133:50101",
    "https": "http://sundayokwu12345:c2Vw96fzFP@216.180.253.133:50101"
}

r = requests.get("https://ipinfo.io/ip", proxies=proxies, timeout=5)
print(r.text)