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
        
        
        

    def __getUserDecks(self):
        url = (
            "https://api.moxfield.com/v2/users/" +
            self.username + "/decks?pageNumber=1&pageSize=99999"
            )
        r = self.session.get(url)
        print("Getting user decks -->", r)
        j = json.loads(r.text)
        # printJson(j)
        return j
    

    def __getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        print(f"Grabbing decklist <{deckId}>")                        #Logging
        r = self.session.get(url)
        jsonGet = json.loads(r.text)

        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = jsonGet["format"]

        if jsonGet["commandersCount"] != 0:
            for card in jsonGet["commanders"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["commanders"][card]

                cardFormat["name"] = card
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            print(url)
            for card in jsonGet["companions"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["companions"][card]
                
                cardFormat["name"] = card
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["companions"].append(cardFormat)

        for card in jsonGet["mainboard"]:
            cardFormat = deepcopy(CardFormatTemplate)
            specificCard = jsonGet["mainboard"][card]

            cardFormat["name"] = card
            cardFormat["quantity"] = specificCard["quantity"]
            cardFormat["set"] = specificCard["card"]["set"].upper()
            cardFormat["setNr"] = specificCard["card"]["cn"]
            deckList["mainboard"].append(cardFormat)

        for card in jsonGet["sideboard"]:
            cardFormat = deepcopy(CardFormatTemplate)
            specificCard = jsonGet["sideboard"][card]

            cardFormat["name"] = card
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

