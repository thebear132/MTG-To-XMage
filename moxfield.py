from utils import *
from copy import deepcopy

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class MoxField:
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath #+ "\\Moxfield"
        
        # Setup a Chrome in headless mode, which is used instead of python-requests as Cloudflare somehow knows and blocks it
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        self.driver = webdriver.Chrome(options=chrome_options)

    def __getUserDecks(self):
        url = "https://api.moxfield.com/v2/users/" + self.username + "/decks?pageNumber=1&pageSize=99999"
        self.driver.get(url)
        raw_response = self.driver.execute_script("return document.body.innerText;")
        j = json.loads(raw_response)
        # printJson(j)
        return j
    
    def __card(self, specificCard):
        cardFormat = deepcopy(CardFormatTemplate)

        cardFormat["name"] = specificCard["card"]["name"]
        cardFormat["quantity"] = specificCard["quantity"]
        cardFormat["set"] = specificCard["card"]["set"].upper()
        cardFormat["setNr"] = specificCard["card"]["cn"]
        cardFormat["layout"] = specificCard["card"]["layout"]
        
        # print("\n", cardFormat["name"], cardFormat["set"], cardFormat["setNr"])
        tmp = cardFormat["setNr"][-1:]
        if tmp.isalpha(): # If promo, convert to non-promo
            cardFormat["setNr"] = cardFormat["setNr"][:-1]
            cardFormat["set"] = cardFormat["set"][1:]
        
        if cardFormat["set"] == "PLST": # If card from the list
            cardFormat["set"], cardFormat["setNr"] = cardFormat["setNr"].split("-")
        
        # print(cardFormat)
        return cardFormat
        

    def __getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # Fetch using Selenium        
        self.driver.get(url)
        raw_response = self.driver.execute_script("return document.body.innerText;")
        jsonGet = json.loads(raw_response)


        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = jsonGet["format"]

        if jsonGet["commandersCount"] != 0:
            for card in jsonGet["commanders"]:
                specificCard = jsonGet["commanders"][card]
                cardFormat = self.__card(specificCard)
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            print(url)
            for card in jsonGet["companions"]:
                specificCard = jsonGet["companions"][card]
                cardFormat = self.__card(specificCard)
                deckList["companions"].append(cardFormat)

        for card in jsonGet["mainboard"]:
            specificCard = jsonGet["mainboard"][card]
            cardFormat = self.__card(specificCard)
            deckList["mainboard"].append(cardFormat)

        for card in jsonGet["sideboard"]:
            specificCard = jsonGet["sideboard"][card]
            cardFormat = self.__card(specificCard)
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

