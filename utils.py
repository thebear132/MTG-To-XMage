from tokenize import String
import json
import os
import re
from copy import deepcopy
import requests
from bs4 import BeautifulSoup   #https://www.crummy.com/software/BeautifulSoup/bs4/doc/#navigating-the-tree
import html
import random
import cloudscraper

def printJson(j):
    print(json.dumps(j, indent=4))


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
    "layout": "normal"  # normal (transform, adventure, split, modal_dfc) (Only split cards have names with //, Fire // Ice)
}

def convertDeckToXmage(deckList):
    # If the format is EDH, make the Commander the only sideboard card
    if deckList["format"] == "commander":
        deckList["sideboard"] = []
        for cmdr in deckList["commanders"]:
            deckList["sideboard"].append(cmdr)

    xDeck = ""  #Add NAME tag NAME:Arcades Aggro
    problematicCards = []
    for card in deckList["mainboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]
        layout = card["layout"]

        if "//" in name and layout != "split":  # Fix adventure cards e.g. Bonecrusher Giant // Stomp => Bonecrusher Giant
            problematicCards.append(name)
            name = name[:name.index("//")-1]

        line = f"{quantity} [{set}:{setNr}] {name}\n"
        xDeck += line
    
    for card in deckList["sideboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]
        layout = card["layout"]

        if "//" in name and layout != "split":
            problematicCards.append(name)
            name = name[:name.index("//")-1]
        
        line = f"SB: {quantity} [{set}:{setNr}] {name}\n"
        xDeck += line

    if len(problematicCards) != 0:
        print("     [!]", len(problematicCards), "card(s) might not have been imported correctly, check your deck.")
        # logging the problematic cards here
    return xDeck

def writeXmageToPath(xmageFolderPath, deckName, format, deckContent):
    #print(xmageFolderPath + "\\" + deckName + ".dck")                    #Logging
    xmageFolderPath = os.path.join(xmageFolderPath, format)
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)

    # Remove bad characters
    deckName = "".join(i for i in deckName if i not in r"\/:*?<>|")
    f = open(os.path.join(xmageFolderPath, deckName) + ".dck", "w", encoding='utf-8')
    f.write(deckContent)
    f.close()




# Moxfield helpers, you can copy them inside your Moxfield class or keep them here idk

def getMoxfieldExportId(deck_id):
    url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}"
    
    scraper = cloudscraper.create_scraper()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    response = scraper.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        exportId = data.get("exportId","")
        # print(exportId)
        return exportId
    
    else:
        print(response.status_code, response.text)
    
    return ""


def getUserDecklistsInfo(username):
    #  @returns: (An array of tuples with deckname and deck id...You may never need the deckname and decide to ditch it,but returning it as well doesn't hurt)
    url = f"https://api.moxfield.com/v2/users/{username}/decks?pageNumber=1&pageSize=99999"
    
    scraper = cloudscraper.create_scraper()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    response = scraper.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        deck_info = []
        for deck in data["data"]:
            deck_name = deck["name"]
            deck_id = deck["publicId"]
            deck_info.append((deck_name, deck_id))
            
        return deck_info
    
    else:
        print(response.status_code, response.text)
    
    return []

def getMoxfieldDecklist(username):
    user_decks = getUserDecklistsInfo(username)
    deck_list = {}
    
    for deck_name, deck_id in user_decks:
        export_id = getMoxfieldExportId(deck_id)
        url = f"https://api2.moxfield.com/v2/decks/all/{deck_id}/export?arenaOnly=false&format=mtgo&exportId={export_id}&pricingProvider=cardkingdom"
        scraper = cloudscraper.create_scraper()

        headers = {
            # TODO - cycle dynamically through UAs
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html; charset=utf-8"
        }

        response = scraper.get(url, headers=headers)
        if response.status_code == 200:
            deck_list[deck_name] = response.text
        else:
            print(f"Failed to fetch deck {deck_name}: {response.status_code}")
        
        for deck_name, deck_list_text in deck_list.items():
            print(f'["{deck_name}": "{deck_list_text}"]')
            
    return deck_list

# Call this like :
# getMoxfieldDecklist("crimxon")
