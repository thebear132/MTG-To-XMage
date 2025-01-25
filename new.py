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
del cj

print(f"Found {len(moxfield_cookies)} Moxfield cookies:", [i.name for i in moxfield_cookies])

for c in moxfield_cookies:
    if c.name == "refresh_token":
        break
else:
    print("Refresh token not found in Moxfield cookies")
    # exit(0)


# Create a session
session = requests.Session()
# session.cookies = moxfield_cookies

useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
session.headers.update({'User-Agent': useragent})
session.proxies.update({"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"})
session.verify = False

url = (
    "https://api.moxfield.com/v2/users/" +
    "thebear132" + "/decks?pageNumber=1&pageSize=99999"
)

r = session.get(url)
print(r)
print(r.text)
j = json.loads(r.text)

exit(0)


# Use refresh_token to retrieve Authorization token
burp0_json={"ignoreCookie": False, "isAppLogin": False}
response = session.post("https://api2.moxfield.com:443/v1/account/token/refresh", json=burp0_json)
# Verify that it worked
if "access_token" not in response.text:
    print(session.cookies)
    print("Didnt find token!")
    exit(0)
# Retrieve Authorization token
access_token = json.loads(response.text)["access_token"]
session.headers.update({"Authorization": "Bearer " + access_token})

# Use Authorization token to access decks
response = session.get("https://api2.moxfield.com:443/v3/decks")
userDecks = json.loads(response.text)["decks"]

domainCascade = userDecks[15] # Get Domain Cascade for testing!
for deck in userDecks:
    if deck["name"] != "Domain Cascade":
        continue

    response = session.get("https://api2.moxfield.com:443/v3/decks/all/" + deck["publicId"])
    jsonGet = json.loads(response.text)
    for card in jsonGet["boards"]["mainboard"]["cards"]:
        specificCard = jsonGet["boards"]["mainboard"]["cards"][card]
        print("Id:", card)

        print("Name", specificCard["card"]["name"])
        print("Quantity", specificCard["quantity"])
        print("Set", specificCard["card"]["set"].upper())
        print("SetNr", specificCard["card"]["cn"])
        # cardFormat["quantity"] = specificCard["quantity"]
        # cardFormat["set"] = specificCard["card"]["set"].upper()
        # cardFormat["setNr"] = specificCard["card"]["cn"]
        # deckList["companions"].append(cardFormat)

        break

    for card in jsonGet["boards"]["sideboard"]:
        specificCard = jsonGet["boards"]["sideboard"][card]

