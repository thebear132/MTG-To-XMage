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
from copy import deepcopy

""" SHIFT + ALT + F -> FIX INDENTATION ERRORS
# https://docs.readthedocs.io/en/stable/api/v2.html
# UDFORSK DERES API BRO. Det er nok en v2 api
Man kunne prøve og fuzz deres api
https://api.moxfield.com/v2/decks/all/	Lister alle public decks på moxfield


_____TODO_____
Enable logging with -v https://stackoverflow.com/questions/6579496/using-print-statements-only-to-debug
Use multiple sites for downloading
    Moxfield - Done
    mtggoldfish - Done
    tappedout
    archideckt
When format is edh, the commander has to be the only card in the sideboard (Moxfield)
"""


def debug(args): # Enable debugging printing
    print("debug")


def printBanner(websiteName):  # Implemented => (moxfield, mtggoldfish). Doom font
    if websiteName == "moxfield":
        print(
            """
___  ___           __ _      _     _ 
|  \/  |          / _(_)    | |   | |
| .  . | _____  _| |_ _  ___| | __| |
| |\/| |/ _ \ \/ /  _| |/ _ \ |/ _` |
| |  | | (_) >  <| | | |  __/ | (_| |
\_|  |_/\___/_/\_\_| |_|\___|_|\__,_|
""")
    elif websiteName == "mtggoldfish":
        print(
            """
___  ____        _____       _     _  __ _     _     
|  \/  | |      |  __ \     | |   | |/ _(_)   | |    
| .  . | |_ __ _| |  \/ ___ | | __| | |_ _ ___| |__  
| |\/| | __/ _` | | __ / _ \| |/ _` |  _| / __| '_ \ 
| |  | | || (_| | |_\ \ (_) | | (_| | | | \__ \ | | |
\_|  |_/\__\__, |\____/\___/|_|\__,_|_| |_|___/_| |_|
            __/ |                                    
           |___/                                     
""")


def printJson(j):
    print(json.dumps(j, indent=4, sort_keys=True))


def logResponse(name, r):  # Logs the request to a .html file for reviewing
    f = open(name, "w")
    text = str(r.status_code) + "\n" + \
        str(r.headers) + "\n\n\n\n" + str(r.text)
    text = text.replace("', '", "',\n'")
    f.write(text)
    f.close()


DeckListTemplate = {  # Remember to deepcopy() when copying this template
    "format": "",       # Format
    "companions": [],   # List of <CardFormatTemplate>
    "commanders": [],   # List of <CardFormatTemplate>
    "mainboard": [],    # List of <CardFormatTemplate>
    "sideboard": []     # List of <CardFormatTemplate>
}
CardFormatTemplate = {
    "quantity": 0,
    "name": "",  # Lightning Bolt
    "set": "",  # M12
    "setNr": "1",  # 65
}


def convertDeckToXmage(deckList):
    # If the format is EDH, make the Commander the only sideboard card
    if deckList["format"] == "commander":
        deckList["sideboard"] = []
        for cmdr in deckList["commanders"]:
            deckList["sideboard"].append(cmdr)

    xDeck = ""
    problematicCards = ""
    for card in deckList["mainboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]

        if "//" in name:  # Fix adventure cards e.g. Bonecrusher Giant // Stomp => Bonecrusher Giant
            problematicCards += name + "| "
            name = name[:name.index("//")-1]
        
        line = f"{quantity} [{set}:{setNr}] {name}\n"
        xDeck += line
    for card in deckList["sideboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]

        if "//" in name:
            problematicCards += "[SB]" + name + "| "
            name = name[:name.index("//")-1]
        
        line = f"SB: {quantity} [{set}:{setNr}] {name}\n"
        xDeck += line
        
    if problematicCards != "":
        print("     [!]", problematicCards.count('|'), "card(s) might not have been imported. Run in verbose mode (-v) for more info")
        #logging the problematic cards here
    return xDeck


def writeXmageToPath(xmageFolderPath, deckName, format, deckContent):
    # print(self.xmageFolderPath + "\\" + deckName + ".dck")                    #Logging
    xmageFolderPath += "\\" + format
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)

    # Remove bad characters
    deckName = "".join(i for i in deckName if i not in "\/:*?<>|")
    f = open(xmageFolderPath + "\\" + deckName + ".dck", "w")
    f.write(deckContent)
    f.close()


class MoxField:
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\Moxfield"

    def __getUserDecks(self):
        url = (
            "https://api.moxfield.com/v2/users/"
            + self.username
            + "/decks?pageNumber=1&pageSize=99999"
        )
        # Logging
        #print(f"Grabbing <{self.username}>'s public decks from " + url)
        r = requests.get(url)
        j = json.loads(r.text)
        return j

    def __getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # print(f"Grabbing decklist <{deckId}>")                        #Logging
        r = requests.get(url)
        jsonGet = json.loads(r.text)

        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = jsonGet["format"]

        if jsonGet["commandersCount"] != 0:
            for cmdr in jsonGet["commanders"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["commanders"][cmdr]

                cardFormat["name"] = cmdr
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            for comp in jsonGet["companions"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["comp"][comp]

                cardFormat["name"] = comp
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["comp"].append(cardFormat)

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
        printBanner("moxfield")
        print("Only public decks are searchable in Moxfield")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks["data"])
        for e in userDecks["data"]:
            print(f"({i}/{total}) " + e["name"] + " " * (50 -
                  len(e["name"]) - len(str(i))) + e["publicUrl"])
            i = i + 1
            deckJson = self.__getDecklist(e["publicId"])
            xDeck = convertDeckToXmage(deckJson)
            writeXmageToPath(self.xmageFolderPath,
                             e["name"], e["format"], xDeck)


class MtgGoldfish:
    mtggoldfishUrl = "https://www.mtggoldfish.com"
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\MtgGoldfish"

    def __getUserDecks(self):
        url = (
            r"https://www.mtggoldfish.com/deck_searches/create?utf8=%E2%9C%93&deck_search[types][]=user&deck_search[player]="
            + self.username
            + "&deck_search[date_range]=10/28/2015%20-%2010/28/2023&deck_search[deck_search_card_filters_attributes][0][type]=maindeck&deck_search[deck_search_card_filters_attributes][1][quantity]=1&deck_search[deck_search_card_filters_attributes][1][type]=maindeck&counter=2&commit=Search"
        )
        r = requests.get(url)
        if r.status_code != 200:
            logResponse("__getUserDecks.log", r)
            print("An error accoured, check folder for logs")

        # (?<=<td><a href=")(/deck/[0-9]{7})">(.*)</a>
        # Match group link and deckname
        regex = re.findall(
            r'(?<=<td><a href=")(/deck/[0-9]{7})">(.*)</a>', r.text)
        deckList = {}
        for e in regex:
            # print(e[0] + " called " + e[1])
            deckList[e[1]] = e[0]

        # Dictionary {'Edh Arcades Aggro deck', '/deck/123qsd'}
        return deckList

    # Does not follow the DeckListTemplate format yet
    def __getDeckList(self, deckName, deckUrl):
        url = f"https://www.mtggoldfish.com{deckUrl}#paper"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.",
        }  # MTGGoldfish gives a 406 if the Accept header is not set properly
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            logResponse("__getDeckList.log", r)
            print("An error accoured, check folder for logs")

        # Filter out the last part of the response
        sortedR = r.text[: r.text.index("<div class='hidden-form'")]

        """f = open("sortedR.log", "w")
        f.write(sortedR)
        f.close()"""

        # Regex for format
        format = re.findall(r"(?:Format: )(.*)", sortedR)[0].lower()
        # Regex for Commanders. #altCommander is for partner
        mainCommander = re.findall(
            r'(?:id="deck_input_commander" value=")(.*)" \/>', sortedR)
        altCommander = re.findall(
            r'(?:id="deck_input_commander_alt" value=")(.*)" \/>', sortedR)
        # If commander found in deck, assign the names
        if len(mainCommander) != 0:
            mainCommander = mainCommander[0]
        if len(altCommander) != 0:
            altCommander = altCommander[0]
        #print("COMMANDERS", mainCommander, "ALT", altCommander)

        # Regex for id, name and set    (?:<td class='text-right'>[\r\n]+)([0-9]{0,2})(?:(?:.|\n){12})(?:.*data-card-id=")(.*)\[(.*)\]
        regexFindCard = r'(?:<td class=\'text-right\'>[\r\n]+)([0-9]{0,2})(?:(?:.|\n){12})(?:.*data-card-id=")(.*)\[(.*)\]'

        # Split into mainboard and sideboard (IF a sideboard exists)
        sideboardDivider = "<th colspan='4'>\nSideboard"
        if sideboardDivider in sortedR:
            mainboard = re.findall(
                regexFindCard, sortedR[: sortedR.index(sideboardDivider)])
            sideboard = re.findall(
                regexFindCard, sortedR[sortedR.index(sideboardDivider):])
        else:
            mainboard = mainboard = re.findall(regexFindCard, sortedR)
            sideboard = []

        # Copy the object by value, instead of by reference
        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = format
        # If cardFormat is declared up here, some weird bug happens? Idk man what the hell

        for card in mainboard:  # MAINBOARD
            # Unescape html encoding like &#39; for "<". Also strip
            name = html.unescape(card[1]).strip()
            # If name contains <timeshifted> or <planeswalker stamp>, remove it
            if "<" in name:
                name = name[:name.index("<")].strip()

            cardFormat = deepcopy(CardFormatTemplate)
            cardFormat["quantity"] = card[0]
            cardFormat["name"] = name.strip()
            cardFormat["set"] = card[2]
            # MTGGoldfish has no value here. Will still work in Xmage
            cardFormat["setNr"] = "-1"

            if name == mainCommander or name == altCommander:
                deckList["commanders"].append(cardFormat)
                #print(name, "Commander found, adding to mainboard")
            else:
                deckList["mainboard"].append(cardFormat)

        for card in sideboard:  # SIDEBOARD
            name = html.unescape(card[1])
            if "<" in name:
                name = name[: name.index("<")]

            cardFormat = deepcopy(CardFormatTemplate)
            cardFormat["quantity"] = card[0]
            cardFormat["name"] = name
            cardFormat["set"] = card[2]
            cardFormat["setNr"] = "-1"
            deckList["sideboard"].append(cardFormat)

        # Access deckList e.g. deckList[0]["name"] => Lightning Bolt
        return deckList

    def Download(self):
        printBanner("mtggoldfish")
        print("Only legal decks are searchable in MtgGoldfish")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks)
        for deckName in userDecks:  # userDecks [Name, url]
            print(f"({i}/{total}) " + deckName + " " * (50 - len(deckName) -
                  len(str(i))) + self.mtggoldfishUrl + userDecks[deckName])
            i = i + 1

            deckList = self.__getDeckList(deckName, userDecks[deckName])
            xDeck = convertDeckToXmage(deckList)
            writeXmageToPath(self.xmageFolderPath, deckName,
                             deckList["format"], xDeck)

        #deckList = self.__getDeckList("Malcolm/Breeches", "/deck/4754316")
        #deckList = self.__getDeckList("Arcades EDH Aggro", "/deck/1430191")
        #xDeck = convertDeckToXmage(deckList)
        #writeXmageToPath(self.xmageFolderPath, deckName, deckList["format"], xDeck)
        a = 2+2


if __name__ == "__main__":
    deckFolder = r"C:\Users\Bear\Desktop\MTG-To-XMage\decks"

    MoxField("thebear132", deckFolder).Download()

    MtgGoldfish("Hypernova", deckFolder).Download()
