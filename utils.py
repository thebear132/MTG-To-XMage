from tokenize import String
import json
import os
import re
from copy import deepcopy
import requests
from bs4 import BeautifulSoup   #https://www.crummy.com/software/BeautifulSoup/bs4/doc/#navigating-the-tree
import html
import random

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
#    "name" : ""         # Name                         Forge need deck inside xDeck (I didn't manage to make it works)
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

def convertDeckToForge(deckList):

    xDeck = ""
    problematicCards = []

    xDeck += "[Main]\n"
    for card in deckList["mainboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]
        layout = card["layout"]

        if "//" in name and layout != "split":  # Fix adventure cards e.g. Bonecrusher Giant // Stomp => Bonecrusher Giant
            problematicCards.append(name)
            name = name[:name.index("//")-1]

        line = f"{quantity} {name}|{set}|[{setNr}]\n"
        xDeck += line
    
    if deckList["sideboard"]:
        xDeck += "[Sideboard]\n"
        for card in deckList["sideboard"]:
            quantity = card["quantity"]
            name = card["name"]
            set = card["set"]
            setNr = card["setNr"]
            layout = card["layout"]

            if "//" in name and layout != "split":
                problematicCards.append(name)
                name = name[:name.index("//")-1]
            
            line = f"{quantity} {name}|{set}|[{setNr}]\n"
            xDeck += line

    if deckList["commanders"]:
        xDeck += "[Commander]\n"
        for card in deckList["commanders"]:
            quantity = card["quantity"]
            name = card["name"]
            set = card["set"]
            setNr = card["setNr"]
            layout = card["layout"]

            if "//" in name and layout != "split":  # Fix adventure cards e.g. Bonecrusher Giant // Stomp => Bonecrusher Giant
                problematicCards.append(name)
                name = name[:name.index("//")-1]

            line = f"{quantity} {name}|{set}|[{setNr}]\n"
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

def writeForgeToPath(xmageFolderPath, deckName, format, deckContent):
    #print(xmageFolderPath + "\\" + deckName + ".dck")                    #Logging
    if format == "tinyLeaders":
        format = "tiny_leaders"     # Forge tiny leaders folder is "tiny_leaders"
    elif format == "historicBrawl":
        format = "brawl"
    elif format not in ["commander","brawl","oathbreaker"]:                 #Forge seems to only support these special formats, others falls inside constructed
        format = "constructed"
    deckContent = "".join(("[metadata]\nName=", deckName, "\n", deckContent)) #Forge needs deck name inside xDeck (Was placed here because I didn't found a variable containing the deck name inside convertDeckToForge()) See line 73
    xmageFolderPath = os.path.join(xmageFolderPath, format)
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)

    # Remove bad characters
    deckName = "".join(i for i in deckName if i not in r"\/:*?<>|")
    f = open(os.path.join(xmageFolderPath, deckName) + ".dck", "w", encoding='utf-8')
    f.write(deckContent)
    f.close()
