import argparse
from tokenize import String
import requests
import random
import json
import logging
import os
import re
import html
from bs4 import BeautifulSoup   #https://www.crummy.com/software/BeautifulSoup/bs4/doc/#navigating-the-tree
from copy import deepcopy


""" SHIFT + ALT + F -> FIX INDENTATION ERRORS
# https://docs.readthedocs.io/en/stable/api/v2.html
# UDFORSK DERES API BRO. Det er nok en v2 api
Man kunne prøve og fuzz deres api
https://api.moxfield.com/v2/decks/all/	Lister alle public decks på moxfield


_____TODO_____
- Enable logging with -v https://stackoverflow.com/questions/6579496/using-print-statements-only-to-debug

- Change the way arguments are passed when running the program. Figure something smarter?
    - If one if the arguments are set, dont run the others

- Archidekt: Update the formatsDict to have all the formats

- convertDeckToXMage: Add the NAME tag to the file. e.g. NAME:Arcades Aggro

Platforms
    Moxfield    - Done
    mtggoldfish - Done
    archideckt  - Done
    tappedout   - Done #Bug with some commander decks, check (Commander But You Never Play Your Commander copy)
    deckstats   - ???
    
"""

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

def debug(args):  # Enable debugging printing
    print("debug")


def printBanner(websiteName):  # Implemented => (moxfield, mtggoldfish). Doom font
    if websiteName == "moxfield":
        print(
            r"""
___  ___           __ _      _     _ 
|  \/  |          / _(_)    | |   | |
| .  . | _____  _| |_ _  ___| | __| |
| |\/| |/ _ \ \/ /  _| |/ _ \ |/ _` |
| |  | | (_) >  <| | | |  __/ | (_| |
\_|  |_/\___/_/\_\_| |_|\___|_|\__,_|
""")
    elif websiteName == "mtggoldfish":
        print(
            r"""
___  ____        _____       _     _  __ _     _     
|  \/  | |      |  __ \     | |   | |/ _(_)   | |    
| .  . | |_ __ _| |  \/ ___ | | __| | |_ _ ___| |__  
| |\/| | __/ _` | | __ / _ \| |/ _` |  _| / __| '_ \ 
| |  | | || (_| | |_\ \ (_) | | (_| | | | \__ \ | | |
\_|  |_/\__\__, |\____/\___/|_|\__,_|_| |_|___/_| |_|
            __/ |                                    
           |___/                                     
""")
    elif websiteName == "archidekt":
        print(
            r"""
  ___           _     _     _      _    _   
 / _ \         | |   (_)   | |    | |  | |  
/ /_\ \_ __ ___| |__  _  __| | ___| | _| |_ 
|  _  | '__/ __| '_ \| |/ _` |/ _ \ |/ / __|
| | | | | | (__| | | | | (_| |  __/   <| |_ 
\_| |_/_|  \___|_| |_|_|\__,_|\___|_|\_\\__|
""")
    elif websiteName == "tappedout":
        print(
            r"""
 _____                          _ _____       _   
|_   _|                        | |  _  |     | |  
  | | __ _ _ __  _ __   ___  __| | | | |_   _| |_ 
  | |/ _` | '_ \| '_ \ / _ \/ _` | | | | | | | __|
  | | (_| | |_) | |_) |  __/ (_| \ \_/ / |_| | |_ 
  \_/\__,_| .__/| .__/ \___|\__,_|\___/ \__,_|\__|
          | |   | |                               
          |_|   |_|                               
""")


def printJson(j):
    print(json.dumps(j, indent=4))


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
    "name": "",         # Lightning Bolt
    "set": "",          # M12
    "setNr": "1",       # 65
}

def convertDeckToXmage(deckList):
    # If the format is EDH, make the Commander the only sideboard card
    if deckList["format"] == "commander":
        deckList["sideboard"] = []
        for cmdr in deckList["commanders"]:
            deckList["sideboard"].append(cmdr)

    xDeck = ""  #Add NAME tag NAME:Arcades Aggro
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
        # logging the problematic cards here
    return xDeck

def writeXmageToPath(xmageFolderPath, deckName, format, deckContent):
    #print(xmageFolderPath + "\\" + deckName + ".dck")                    #Logging
    xmageFolderPath = os.path.join(xmageFolderPath, format)
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)

    # Remove bad characters
    deckName = "".join(i for i in deckName if i not in "\/:*?<>|")
    f = open(os.path.join(xmageFolderPath, deckName) + ".dck", "w", encoding='utf-8')
    f.write(deckContent)
    f.close()


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
        # Logging
        print(f"Grabbing <{self.username}>'s public decks from " + url)
        # proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
        # response = requests.get('http://httpbin.org/headers')
        # https://www.th3r3p0.com/random/python-requests-and-burp-suite.html
        
        r = requests.get(url, headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
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

                cardFormat["name"] = cmdr
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            print(url)
            for comp in jsonGet["companions"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["companions"][comp]
                
                cardFormat["name"] = comp
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

        # Match group link and deckname
        regex = re.findall(
            r'(?<=<td><a href=")(/deck/[0-9]{7})">(.*)</a>', r.text)
        userDecks = {}
        for e in regex:
            # print(e[0] + " called " + e[1])
            userDecks[e[1]] = e[0]

        # Dictionary {'Edh Arcades Aggro deck', '/deck/123qsd'}
        return userDecks

    def __getDeckList(self, deckUrl):
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

            deckList = self.__getDeckList(userDecks[deckName])
            xDeck = convertDeckToXmage(deckList)
            writeXmageToPath(self.xmageFolderPath, deckName,
                             deckList["format"], xDeck)

        #deckList = self.__getDeckList("Malcolm/Breeches", "/deck/4754316")
        #deckList = self.__getDeckList("Arcades EDH Aggro", "/deck/1430191")


class Archidekt:
    archidektUrl = "https://archidekt.com"
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\Archidekt"

    def __getUserDecks(self):
        # https://archidekt.com/search/decks?orderBy=-createdAt&owner=FastHandsTam&ownerexact=true
        url = (
            "https://archidekt.com/api/decks/cards/?orderBy=-createdAt&owner=" +
            self.username + "&ownerexact=true&pageSize=48"
        )
        #print("Getting user decks at = " + url) #Logging

        r = requests.get(url)
        j = json.loads(r.text)
        #f = open("archidektDecks.out", "w"); f.write(json.dumps(j)); f.close()
        userDecks = {}
        for e in j["results"]:
            # {"Kalamax Control": "123567"}
            userDecks[e["name"]] = str(e["id"])
        # printJson(userDecks)
        return userDecks

    def __getDecklist(self, deckId):
        # https://archidekt.com/api/decks/ ID /small/
        url = f"https://archidekt.com/api/decks/{deckId}/small/"

        # print(f"Grabbing decklist <{deckId}> {url}")                        #Logging
        r = requests.get(url)
        jsonGet = json.loads(r.text)

        formatsDict = {  # deckFormat comes in id, it has to be translated
            1: "idk1",
            3: "commander",
            15: "pioneer",
            16: "historic"
        }

        deckList = deepcopy(DeckListTemplate)
        # Skal konverteres fra tal til string
        deckList["format"] = formatsDict[jsonGet["deckFormat"]]

        for card in jsonGet["cards"]:
            cardFormat = deepcopy(CardFormatTemplate)
            cardFormat["name"] = card["card"]["oracleCard"]["name"]
            cardFormat["quantity"] = card["quantity"]
            cardFormat["set"] = card["card"]["edition"]["editioncode"].upper()
            cardFormat["setNr"] = "-1"

            if card["categories"][0] == "Commander":
                deckList["commanders"].append(cardFormat)
            elif card["categories"][0] == "Companion":
                deckList["companions"].append(cardFormat)
            elif card["categories"][0] == "Sideboard":
                deckList["sideboard"].append(cardFormat)
            else:
                deckList["mainboard"].append(cardFormat)
        return deckList

    def Download(self):
        printBanner("archidekt")
        print("Only public decks are searchable in Archidekt")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks)
        for deckName in userDecks:
            print(f"({i}/{total}) " + deckName + " " * (50 - len(deckName) -
                  len(str(i))) + self.archidektUrl + "/decks/" + userDecks[deckName])
            i = i + 1
            deckList = self.__getDecklist(userDecks[deckName])
            xDeck = convertDeckToXmage(deckList)
            writeXmageToPath(self.xmageFolderPath, deckName,
                             str(deckList["format"]), xDeck)


class Tappedout:
    tappedoutUrl = "https://tappedout.net/"
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath + "\\Tappedout"

    def __getUserDecks(self):
        # https://tappedout.net/users/Hypernova/mtg-decks/   Personal, also works? (Using)
        # https://tappedout.net/users/Hypernova/             Public
        url = (
            f"https://tappedout.net/users/{self.username}/mtg-decks/"
        )
        #print("Getting user decks at = " + url)

        r = requests.get(url)

        # Find name and link in 2 groups
        regex = re.findall(
            r'<a title="mtg decks - (.*)" href="/mtg-decks/(.*)/">', r.text)
        userDecks = {}
        for deck in regex:
            userDecks[deck[0]] = deck[1]
        # "Test": "15-09-18-kaI-test"
        
        return userDecks

    def __getDecklist(self, deckId):
        url = f"https://tappedout.net/mtg-decks/{deckId}/"

        #print(f"Grabbing decklist <{deckId}> {url}")  # Logging
        r = requests.get(url)
        """f = open("LordXander.html", "w")
        f.write(r.text)
        f.close()"""
        
        deckList = deepcopy(DeckListTemplate)
        #Format should maybe be retrieved from this line?   Legality This deck is Commander / EDH legal.
        #Depends on if the "Commander / EDH" tag is on every deck, or its missing in some of the decks
        deckList["format"] = re.findall(r'(?:<a class="btn btn-success btn-xs").*">(.*)\n', r.text)[0].lower().strip()
        if "commander" in deckList["format"].lower() or "edh" in deckList["format"].lower():
            deckList["format"] = "commander"
        deckList["format"] = deckList["format"].replace('*', '')
        
        #Find commanders and companion with beautifulsoup
        soup = BeautifulSoup(r.content, 'html.parser')
        
        mainCommander, altCommander = "", ""
        mainCompanion = ""
        h3Tags = soup.find_all('h3')
        for h3 in h3Tags:
            if "commander" in h3.text.lower():
                #print("Commanders found")
                legendary = h3.find_parent().find_all(class_="card-type-legendary")
                mainCommander = legendary[0].a['data-name']
                if len(legendary) == 2:
                    altCommander = legendary[1].a['data-name']
        
            if "companion" in h3.text.lower():
                #print("Found companion")
                parent = h3.find_parent()
                mainCompanion = parent.find(class_="card-type-legendary").a['data-name']
        
        
        #We need to split the mainboard and the sideboard up, they are seperated by 2 newlines
        cards = soup.find(id='mtga-textarea').text
        if "\n\n" in cards:     #If there is a sideboard
            mainboardHTML = cards[:cards.index('\n\n')].strip()
            sideboardHTML = cards[cards.index('\n\n'):].strip()
        else:                   #if there is NO sideboard
            mainboardHTML = cards
        
        # Find all cards with quantity, name, set and setNr
        mainboard = re.findall('([0-9]{1,2}) (.*) \(([0-9a-zA-Z]{1,6})\) ([0-9]{1,4})', mainboardHTML)
        sideboard = re.findall('([0-9]{1,2}) (.*) \(([0-9a-zA-Z]{1,6})\) ([0-9]{1,4})', sideboardHTML)
        for card in mainboard:
            cardFormat = deepcopy(CardFormatTemplate)
            cardFormat["quantity"] = card[0]
            cardFormat["name"] = card[1]
            cardFormat["set"] = card[2]
            cardFormat["setNr"] = card[3]
            
            if cardFormat["name"] == mainCommander or cardFormat["name"] == altCommander:   #If any of the cards are a companion
                deckList["commanders"].append(cardFormat)
            else:
                deckList["mainboard"].append(cardFormat)
            
        for card in sideboard:
            cardFormat = deepcopy(CardFormatTemplate)
            cardFormat["quantity"] = card[0]
            cardFormat["name"] = card[1]
            cardFormat["set"] = card[2]
            cardFormat["setNr"] = card[3]

            
            if cardFormat["name"] == mainCompanion:
                deckList["companions"].append(cardFormat)
            else:
                deckList["sideboard"].append(cardFormat)
        
        #printJson(deckList)
        return deckList

    def Download(self):
        printBanner("tappedout")
        print("Only public decks are searchable in Tappedout")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks)
        for deckName in userDecks:
            print(f"({i}/{total}) " + deckName + " " * (50 - len(deckName) -
                  len(str(i))) + self.tappedoutUrl + "/mtg-decks/" + userDecks[deckName])
            i = i + 1
            
            deckList = self.__getDecklist(userDecks[deckName])
            xDeck = convertDeckToXmage(deckList)
            writeXmageToPath(self.xmageFolderPath, deckName, deckList["format"], xDeck)
        
        #self.__getDecklist("commander-but-you-never-play-your-commander-copy-4")
        #self.__getDecklist("yorion-enchantments-1")
        #self.__getDecklist("breeches-malcolm-enter-a-bar")

# Needs to be changed with -v/-vv/-vvv
# Critical, Error, Warning, Info, Debug
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.ERROR)


def createArgs():  # Customise the argument handler
    parser = argparse.ArgumentParser(
        description='MTG-To-Xmage | Download your online MTG decks to the XMage format')
    # Moxfield username
    parser.add_argument('-moxfield', metavar="username",
                        help='Your username for Moxfield')
    # MtgGoldfish username
    parser.add_argument('-mtggoldfish', metavar="username",
                        help='Your username for MtgGoldfish')
    # Archidekt username
    parser.add_argument('-archidekt', metavar="username",
                        help='Your username for Archidekt')
    # Tappedout username
    parser.add_argument('-tappedout', metavar="username",
                        help='Your username for Tappedout')

    # Path to folder
    parser.add_argument('-o', metavar="path",
                        help='Path to the folder to download your decks to')

    # Verbose mode
    parser.add_argument('-v', action='store_true', help='Verbose mode')
    # Super Verbose mode
    parser.add_argument('-vv', action='store_true', help='Super Verbose mode')

    # If no arguments were submitted, print help
    #args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    args = parser.parse_args()
    return args


def main():
    args = createArgs()
    if args.v:
        print("Verbose mode")
    elif args.vv:
        print("Super verbose mode")
    """
    logging.debug("Debug")
    logging.info("Info")
    logging.warning("Warning")
    logging.error("Error")
    logging.critical("Critical")
    """

    config = {"folder": "", "moxfield": "",
              "mtggoldfish": "", "archidekt": "", "tappedout": ""}
    if os.path.exists("./config.json"):  # If there exists a
        tmp = open("./config.json", "r").read()
        config = json.loads(tmp)

    if args.o is not None:              # If -o [path] is set, update the value
        config["folder"] = args.o
    else:
        if config["folder"] == "":
            config["folder"] = r"./decks"

    if args.moxfield is not None:
        print("Moxfield set")
        config["moxfield"] = args.moxfield
    if args.mtggoldfish is not None: 
        print("MtgGoldfish set")
        config["mtggoldfish"] = args.mtggoldfish
    if args.archidekt is not None:
        print("Archidekt set")
        config["archidekt"] = args.archidekt
    if args.tappedout is not None:
        print("Tappedout set")
        config["tappedout"] = args.tappedout

    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4))
        f.close()

    # printJson(config)
    if config["moxfield"] != "":  # Is config has a username for moxfield, start downloading
        print("Starting Moxfield | " + config["moxfield"])
        MoxField(config["moxfield"], config["folder"]).Download()
    if config["mtggoldfish"] != "":
        print("Starting MtgGoldfish | " + config["mtggoldfish"])
        MtgGoldfish(config["mtggoldfish"], config["folder"]).Download()
    if config["archidekt"] != "":
        print("Starting Archidekt | " + config["archidekt"])
        Archidekt(config["archidekt"], config["folder"]).Download()         #FastHandsTam
    if config["tappedout"] != "":
        print("Starting Tappedout | " + config["tappedout"])
        Tappedout(config["tappedout"], config["folder"]).Download()

if __name__ == "__main__":
    main()





#700