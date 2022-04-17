from ast import MatchSingleton
from cgitb import html
from pip import main
import requests
import json
import logging
import sys
import os
import re
import html
""" SHIFT + ALT + F -> FIX INDENTATION ERRORS
# https://docs.readthedocs.io/en/stable/api/v2.html
# UDFORSK DERES API BRO. Det er nok en v2 api
Man kunne prøve og fuzz deres api
https://api.moxfield.com/v2/decks/all/	Lister alle public decks på moxfield


_____TODO_____
Enable logging with -v https://stackoverflow.com/questions/6579496/using-print-statements-only-to-debug
Use multiple sites for downloading
    Moxfield - Done
    mtggoldfish - Halfway
    tappedout
    archideckt
When format is edh, the commander has to be the only card in the sideboard (Moxfield)
"""


def debug(args):
    print("debug")

def printBanner(websiteName): #Current prints (moxfield, mtggoldfish)
    if websiteName == "moxfield":
        print("""
___  ___           __ _      _     _ 
|  \/  |          / _(_)    | |   | |
| .  . | _____  _| |_ _  ___| | __| |
| |\/| |/ _ \ \/ /  _| |/ _ \ |/ _` |
| |  | | (_) >  <| | | |  __/ | (_| |
\_|  |_/\___/_/\_\_| |_|\___|_|\__,_|
""")
    elif websiteName == "mtggoldfish":
        print("""
___  ________ _____ _____       _     _  __ _     _     
|  \/  |_   _|  __ \  __ \     | |   | |/ _(_)   | |    
| .  . | | | | |  \/ |  \/ ___ | | __| | |_ _ ___| |__  
| |\/| | | | | | __| | __ / _ \| |/ _` |  _| / __| '_ \ 
| |  | | | | | |_\ \ |_\ \ (_) | | (_| | | | \__ \ | | |
\_|  |_/ \_/  \____/\____/\___/|_|\__,_|_| |_|___/_| |_|
""")

def printJson(j):
    print(json.dumps(j, indent=4, sort_keys=True))

def logResponse(name, r):           #Logs the request to a .html file for reviewing
        f = open(name, "w")
        text = str(r.status_code) + "\n" + str(r.headers) + "\n\n\n\n" + str(r.text)
        text = text.replace('\', \'', '\',\n\'')
        f.write(text)
        f.close()

def writeDeckToPath(xmageFolderPath, deckName, format, deckContent):
    # print(self.xmageFolderPath + "\\" + deckName + ".dck")                    #Logging
    xmageFolderPath += "\\" + format
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)
    
    deckName = "".join(i for i in deckName if i not in "\/:*?<>|")              #Remove bad characters    
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

    def __convertDeckToXmage(self, deckJson):
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
        printBanner("moxfield")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks["data"])
        for e in userDecks["data"]:
            print(f"({i}/{total}) " + e["name"] + " "*(50-len(e["name"])-len(str(i))) + e["publicUrl"])
            i = i + 1
            deckJson = self.__getDecklist(e["publicId"])
            xDeck = self.__convertDeckToXmage(deckJson)

            writeDeckToPath(self.xmageFolderPath, e["name"], e["format"], xDeck)



class MtgGoldfish():
    mtggoldfishUrl = "https://www.mtggoldfish.com"
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\MtgGoldfish"

    def __getUserDecks(self):
        url = r"https://www.mtggoldfish.com/deck_searches/create?utf8=%E2%9C%93&deck_search[types][]=user&deck_search[player]=" + self.username + "&deck_search[date_range]=10/28/2015%20-%2010/28/2023&deck_search[deck_search_card_filters_attributes][0][type]=maindeck&deck_search[deck_search_card_filters_attributes][1][quantity]=1&deck_search[deck_search_card_filters_attributes][1][type]=maindeck&counter=2&commit=Search"
        r = requests.get(url)
        if r.status_code != 200:
            logResponse("__getUserDecks.log", r)
            print("An error accoured, check folder for logs")
        
        print("Only legal decks are searchable in MtgGoldfish")
        #(?<=<td><a href=")(/deck/[0-9]{7})">(.*)</a>
        regex = re.findall(r'(?<=<td><a href=")(/deck/[0-9]{7})">(.*)</a>', r.text) #Match group link and deckname
        deckList = {}
        for e in regex:
            #print(e[0] + " called " + e[1])
            deckList[e[1]] = e[0]
        
        return deckList                                 #Dictionary {'Edh Arcades', '/deck/123qsd'}
    
    def __getDeckList(self, deckName, deckUrl):
        url = f"https://www.mtggoldfish.com{deckUrl}#paper"
        print("Getting", deckName, "at", url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0."
        }       #MTGGoldfish gives a 406 if the Accept header is not set properly
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            logResponse("__getDeckList.log", r)
            print("An error accoured, check folder for logs")
        
        #Filter out the last part of the response
        sortedR = r.text[:r.text.index("<div class='hidden-form'")]
        
        """f = open(deckUrl[6:] + ".log", "w")
        f.write(sortedR)
        f.close()"""

        #Regex for format
        format = re.findall(r'(?:Format: )(.*)', sortedR)[0].lower()
        
        #Regex for id, name and set    (?:<td class='text-right'>[\r\n]+)([0-9]{0,2})(?:(?:.|\n){12})(?:.*data-card-id=")(.*)\[(.*)\]
        regexFindCard = r'(?:<td class=\'text-right\'>[\r\n]+)([0-9]{0,2})(?:(?:.|\n){12})(?:.*data-card-id=")(.*)\[(.*)\]'
        #Split into mainboard and sideboard
        mainboard = re.findall(regexFindCard, sortedR[:sortedR.index("Sideboard")])
        sideboard = re.findall(regexFindCard, sortedR[sortedR.index("Sideboard"):])
        
        print("FORMAT =", format, "| Mainboard Len", len(mainboard), "Sideboard Len", len(sideboard))

        deckList = {
            "format": format,
            "mainboard": [],
            "sideboard": []
        }

        for card in mainboard: #MAINBOARD
            name = html.unescape(card[1])   #Unescape html encoding like &#39; for "<"
            if "<" in name:                         #If name contains <timeshifted> or <planeswalker stamp>, remove it
                name = name[:name.index("<")]
            temp = {"quantity": card[0], "name": name.strip(), "set": card[2], }
            deckList["mainboard"].append(temp)

        for card in sideboard:  #SIDEBOARD
            name = html.unescape(card[1])
            if "<" in name:
                name = name[:name.index("<")]
            temp = {"quantity": card[0], "name": name.strip(), "set": card[2], }
            deckList["sideboard"].append(temp)
        
        return deckList #Access with e.g. deckList[0]["name"] => Lightning Bolt

    def __convertDeckToXmage(self, deckList):
        print("FORMAT:", deckList["format"], "!")
        if "commander" == deckList["format"]: #If format EDH, make Commander the only sideboard card
            deckList["sideboard"] = []
            deckList["sideboard"].append(deckList["mainboard"][0])
            deckList["mainboard"].pop(0)
        
        xDeck = ""
        for card in deckList["mainboard"]:
            quantity = card["quantity"]
            set = card["set"]
            name = card["name"]
            line = f"{quantity} [{set}:1] {name}\n"
            xDeck += line
        for card in deckList["sideboard"]:
            quantity = card["quantity"]
            set = card["set"]
            name = card["name"]
            line = f"SB: {quantity} [{set}:1] {name}\n"
            xDeck += line
        return xDeck
        
    def Download(self):
        printBanner("mtggoldfish")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks)
        for deck in userDecks:
            print(f"({i}/{total}) " + deck + " "*(50-len(deck)-len(str(i))) + self.mtggoldfishUrl + userDecks[deck])
            i = i + 1
        
            deckList = self.__getDeckList(userDecks[deck], deck)
            xDeck = self.__convertDeckToXmage(deckList)
            writeDeckToPath(self.xmageFolderPath, userDecks[deck], deckList["format"], xDeck)


"""
deckList = self.__getDeckList(list(userDecks.keys())[id], list(userDecks.values())[id])
xDeck = self.__convertDeckToXmage(deckList)
deckName = "".join(i for i in list(userDecks.keys())[id] if i not in "\/:*?<>|")
writeDeckToPath(self.xmageFolderPath, deckName, deckList["format"], xDeck)
"""


if __name__ == "__main__":
    deckFolder = r"C:\Users\Bear\Desktop\MTG-To-XMage\decks"

    
    #print("-"*50 + "MOXFIELD" + "-"*50)
    MoxField("thebear132", deckFolder).Download()

    #print("-"*50 + "MTGGOLDFISH" + "-"*50)
    MtgGoldfish("Hypernova", deckFolder).Download()
