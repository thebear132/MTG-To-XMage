import browsercookie
import requests
import json


# Import cookies from your default browser
cj = browsercookie.load()

# Set the session's cookies
moxfield_cookies = requests.cookies.RequestsCookieJar()
for cookie in cj:
    if 'moxfield.com' in cookie.domain:
        moxfield_cookies.set_cookie(cookie)
else:
    print("Moxfield cookies not found in browsers?")
    exit(0)
del cj

for c in moxfield_cookies:
    if c.name == "refresh_token":
        break
else:
    print("Refresh token not found")
    exit(0)

# Create a session
session = requests.Session()
session.cookies = moxfield_cookies

proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
session.headers.update({'User-Agent': useragent})
session.proxies.update(proxies)
session.verify = False

print("COOKIES:\n", session.cookies)
burp0_json={"ignoreCookie": False, "isAppLogin": False}
response = session.post("https://api2.moxfield.com:443/v1/account/token/refresh", json=burp0_json)

# Print the response
if "access_token" not in response.text:
    print(session.cookies)
    print("Didnt find token!")
    exit(0)
access_token = json.loads(response.text)["access_token"]
session.headers.update({"Authorization": "Bearer " + access_token})
print(session.cookies)

response = session.get("https://api2.moxfield.com:443/v3/decks")
userDecks = json.load(response.text)["decks"]


