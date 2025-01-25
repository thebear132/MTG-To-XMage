from utils import *
from copy import deepcopy


user_agent_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; Trident/5.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0; MDDCJS)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
]

class MoxField:
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath #+ "\\Moxfield"
        
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
            exit(0)

        # Create a session object used for requests
        self.session = requests.Session()
        self.session.cookies = moxfield_cookies
        useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
        self.session.headers.update({'User-Agent': useragent})
        self.session.proxies.update({"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"})
        self.session.verify = False
        

    def __getUserDecks(self):
        # Use refresh_token to retrieve Authorization token
        burp0_json={"ignoreCookie": False, "isAppLogin": False}
        response = self.session.post("https://api2.moxfield.com:443/v1/account/token/refresh", json=burp0_json)
        # Verify that it worked
        if "access_token" not in response.text:
            print(self.session.cookies)
            print("Didnt find token!")
            exit(0)
        # Retrieve Authorization token
        access_token = json.loads(response.text)["access_token"]
        self.session.headers.update({"Authorization": "Bearer " + access_token})

        # Use Authorization token to access decks
        response = self.session.get("https://api2.moxfield.com:443/v3/decks")
        userDecks = json.loads(response.text)["decks"]
        "____________________"
        
        j = json.loads(r.text)
        # printJson(j)
        return j

    def __getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # print(f"Grabbing decklist <{deckId}>")                        #Logging
        r = requests.get(url, headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        jsonGet = json.loads(r.text)

        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = jsonGet["format"]

        if jsonGet["commandersCount"] != 0:
            for cmdr in jsonGet["commanders"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["commanders"][cmdr]

                cardFormat["name"] = specificCard["card"]["name"]
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            print(url)
            for comp in jsonGet["companions"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["companions"][comp]
                
                cardFormat["name"] = specificCard["card"]["name"]
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["companions"].append(cardFormat)

        for card in jsonGet["boards"]["mainboard"]:
            cardFormat = deepcopy(CardFormatTemplate)
            specificCard = jsonGet["boards"]["mainboard"][card]

            cardFormat["name"] = specificCard["card"]["name"]
            cardFormat["quantity"] = specificCard["quantity"]
            cardFormat["set"] = specificCard["card"]["set"].upper()
            cardFormat["setNr"] = specificCard["card"]["cn"]
            deckList["mainboard"].append(cardFormat)

        for card in jsonGet["boards"]["sideboard"]:
            cardFormat = deepcopy(CardFormatTemplate)
            specificCard = jsonGet["boards"]["sideboard"][card]

            cardFormat["name"] = specificCard["card"]["name"]
            cardFormat["quantity"] = specificCard["quantity"]
            cardFormat["set"] = specificCard["card"]["set"].upper()
            cardFormat["setNr"] = specificCard["card"]["cn"]
            deckList["sideboard"].append(cardFormat)

        return deckList

    def Download(self):
        # printBanner("moxfield")
        print("Only public decks are searchable in Moxfield")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks["data"])
        for deckName in userDecks["data"]:
            print(f"({i}/{total}) " + deckName["name"] + " " * (50 -
                  len(deckName["name"]) - len(str(i))) + deckName["publicUrl"])
            i = i + 1
            deckJson = self.__getDecklist(deckName["publicId"])
            xDeck = convertDeckToXmage(deckJson)
            writeXmageToPath(self.xmageFolderPath,
                             deckName["name"], deckName["format"], xDeck)

