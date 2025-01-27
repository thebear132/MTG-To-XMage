import browser_cookie3 as bc3
import requests
import re
from time import sleep
import json


cookiejar = bc3.firefox(domain_name="moxfield.com")
proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

resp = requests.get('https://moxfield.com', cookies=cookiejar, proxies=proxies, verify=False, headers={'User-Agent': useragent})
print("Initial headers", resp.headers)

sleep(1)

burp0_url = "https://api2.moxfield.com:443/v1/account/token/refresh"
burp0_headers = {"User-Agent": useragent, "Content-Type": "application/json"}
burp0_json={"ignoreCookie": False, "isAppLogin": False}
getAuth = requests.post(burp0_url, headers=burp0_headers, cookies=cookiejar, json=burp0_json, proxies=proxies, verify=False)
print(getAuth)
a = json.loads(getAuth.text)
print(a)
print(a["access_token"])


resp = requests.get('https://api2.moxfield.com/v3/decks', cookies=cookiejar, proxies=proxies, verify=False, headers={'User-Agent': useragent, "Authorization": a["access_token"]})
print(resp.status_code)
print(resp.text)
