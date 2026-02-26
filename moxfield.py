from utils import *
from copy import deepcopy

from playwright.sync_api import sync_playwright
import subprocess


class MoxField:
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath #+ "\\Moxfield"
        
        # Playwright: Install Firefox driver automatically with
        subprocess.run(["python", "-m", "playwright", "install", "firefox"], check=True)
        # Start Playwright and launch browser
        self.p = sync_playwright().start()
        self.browser = self.p.firefox.launch()
        
    def __del__(self):
        # Close browser and stop Playwright
        self.browser.close()
        self.p.stop()

    def __getUserDecks(self):
        url = "https://api.moxfield.com/v2/users/" + self.username + "/decks?pageNumber=1&pageSize=99999"
        page = self.browser.new_page()
        page.goto(url)
        raw_response = page.inner_html("pre")
        j = json.loads(raw_response)
        # printJson(j)
        return j
    
    def __formatCard(self, specificCard):
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
        elif cardFormat["setNr"][-1:] =="★": # Forge doesn't support foils → need to remove "★". 
            cardFormat["setNr"] = cardFormat["setNr"][:-1]

        
        if cardFormat["set"] == "PLST": # If card from the list
            cardFormat["set"], cardFormat["setNr"] = cardFormat["setNr"].split("-")
        
        # print(cardFormat)
        return cardFormat
        

    def __getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # Fetch using Playwright        
        page = self.browser.new_page()
        page.goto(url)
        raw_response = page.inner_html("pre")
        jsonGet = json.loads(raw_response)


        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = jsonGet["format"]
#        decklist["name"] = jsonGet["name"]     Forge need deck inside xDeck (I didn't manage to make it works) See Utils line 73

        if jsonGet["commandersCount"] != 0:
            for card in jsonGet["commanders"]:
                specificCard = jsonGet["commanders"][card]
                cardFormat = self.__formatCard(specificCard)
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            print(url)
            for card in jsonGet["companions"]:
                specificCard = jsonGet["companions"][card]
                cardFormat = self.__formatCard(specificCard)
                deckList["companions"].append(cardFormat)

        for card in jsonGet["mainboard"]:
            specificCard = jsonGet["mainboard"][card]
            cardFormat = self.__formatCard(specificCard)
            deckList["mainboard"].append(cardFormat)

        for card in jsonGet["sideboard"]:
            specificCard = jsonGet["sideboard"][card]
            cardFormat = self.__formatCard(specificCard)
            deckList["sideboard"].append(cardFormat)

        for card in jsonGet["signatureSpells"]:             #Forge oathbreaker signature spell's are placed inside [commander] section
            specificCard = jsonGet["signatureSpells"][card]
            deckList["commanders"].append(cardFormat)

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
            xDeck = convertDeckToForge(deckJson)                                #Hard replace with Forge function. I don't know how args works
            writeForgeToPath(self.xmageFolderPath,                              #Hard replace with Forge function. I don't know how args works
                             deckName["name"], deckName["format"], xDeck)

