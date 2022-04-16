import requests
import json
import logging
import sys
import os
""" SHIFT + ALT + F -> FIX INDENTATION ERRORS
# https://docs.readthedocs.io/en/stable/api/v2.html
# UDFORSK DERES API BRO. Det er nok en v2 api
Man kunne prøve og fuzz deres api
https://api.moxfield.com/v2/decks/all/	Lister alle public decks på moxfield


TODO. Enable logging with -v https://stackoverflow.com/questions/6579496/using-print-statements-only-to-debug
Use multiple sites for downloading
    Moxfield - Done
    mtggoldfish
    tappedout
    archideckt
"""


def debug(args):
    print("debuyg")


def printJson(j):
    print(json.dumps(j, indent=4, sort_keys=True))


def writeDeckToPath(xmageFolderPath, deckName, deckContent):
    # print(self.xmageFolderPath + "\\" + deckName + ".dck")                      #Logging
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)
    f = open(xmageFolderPath + "\\" + deckName + ".dck", "w")
    f.write(deckContent)
    f.close()


class MoxField():
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\Moxfield"

    def __getUserDecks(self):
        url = "https://api.moxfield.com/v2/users/" + \
            self.username + "/decks?pageNumber=1&pageSize=99999"
        # Logging
        print(f"Grabbing <{self.username}>'s public decks from " + url)
        r = requests.get(url)
        j = json.loads(r.text)
        return j

    def __getDecklist(self, deckId):
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # print(f"Grabbing decklist <{deckId}>")                                    #Logging
        r = requests.get(url)
        j = json.loads(r.text)
        return j

    def __convertDeckToX(self, deckJson):
        xDeck = ""
        for card in deckJson["mainboard"]:
            c = deckJson["mainboard"][card]
            cc = c["card"]
            quantity = c["quantity"]
            set = cc["set"].upper()
            setNr = cc["cn"]
            name = cc["name"]
            # 1 [IKO:40] Anticipate
            line = f"{quantity} [{set}:{setNr}] {name}\n"
            xDeck += line
        for card in deckJson["sideboard"]:
            c = deckJson["sideboard"][card]
            cc = c["card"]
            quantity = c["quantity"]
            set = cc["set"].upper()
            setNr = cc["cn"]
            name = cc["name"]
            # SB: 1 [IKO:40] Anticipate
            line = f"SB: {quantity} [{set}:{setNr}] {name}\n"
            xDeck += line
        return xDeck

    def Download(self):
        userDecks = self.__getUserDecks()
        i, total = 1, str(len(userDecks["data"]))
        for e in userDecks["data"]:
            print(f"({i}/{total}) " + e["name"] + " " *
                  (50-len(e["name"])-len(str(i))) + e["publicUrl"])
            i = i + 1
            deckJson = self.__getDecklist(e["publicId"])
            xDeck = self.__convertDeckToX(deckJson)

            # Remove bad characters from deckname
            deckName = "".join(i for i in e["name"] if i not in "\/:*?<>|")
            writeDeckToPath(self.xmageFolderPath + "\\" + e["format"], deckName, xDeck)


class MtgGoldfish():
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\MtgGoldfish"
    
    def Download(self):         #https://www.mtggoldfish.com/deck_searches/create?utf8=%E2%9C%93&deck_search%5Bname%5D=&deck_search%5Bformat%5D=&deck_search%5Btypes%5D%5B%5D=&deck_search%5Btypes%5D%5B%5D=tournament&deck_search%5Btypes%5D%5B%5D=user&deck_search%5Bplayer%5D=Hypernova&deck_search%5Bdate_range%5D=04%2F02%2F2000+-+04%2F16%2F2022&deck_search%5Bdeck_search_card_filters_attributes%5D%5B0%5D%5Bcard%5D=&deck_search%5Bdeck_search_card_filters_attributes%5D%5B0%5D%5Bquantity%5D=1&deck_search%5Bdeck_search_card_filters_attributes%5D%5B0%5D%5Btype%5D=maindeck&deck_search%5Bdeck_search_card_filters_attributes%5D%5B1%5D%5Bcard%5D=&deck_search%5Bdeck_search_card_filters_attributes%5D%5B1%5D%5Bquantity%5D=1&deck_search%5Bdeck_search_card_filters_attributes%5D%5B1%5D%5Btype%5D=maindeck&counter=2&commit=Search
                                #Get user decks
        print("Downloading")

if __name__ == "__main__":
    username = "thebear132"
    deckPath = r"C:\Users\Bear\Desktop\MTG-To-XMage\decks"

    #MOXFIELD
    print("-"*50 + "MOXFIELD" + "-"*50)
    #MoxField(username, deckPath).Download()

    #MtgGoldfish
    print("-"*50 + "MTGGOLDFISH" + "-"*50)
    MtgGoldfish(username, deckPath).Download()
