import requests

url = (
            "https://api.moxfield.com/v2/users/" +
            "thebear132" + "/decks?pageNumber=1&pageSize=99999"
        )
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'}
proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
r = requests.get(url, headers=headers, proxies=proxies, verify=False)
print(r.text)

