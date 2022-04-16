import requests
import json
import logging, sys
"""
#https://docs.readthedocs.io/en/stable/api/v2.html
#UDFORSK DERES API BRO. Det er nok en v2 api
Man kunne prøve og fuzz deres api
https://api.moxfield.com/v2/decks/all/	Lister alle public decks på moxfield


TODO. Enable logging with -v
https://stackoverflow.com/questions/6579496/using-print-statements-only-to-debug
Use multiple sites for downloading
	Moxfield
	tappedout
	mtggoldfish
	archideckt

"""


def debug(args):
	print("debuyg")

def printJson(j):
	print(json.dumps(j, indent=4, sort_keys=True))

def getUserDecks(username):
	url = "https://api.moxfield.com/v2/users/" + username + "/decks?pageNumber=1&pageSize=99999"
	print(f"Grabbing <{username}>'s public decks from " + url)
	r = requests.get(url)
	j = json.loads(r.text)
	return j

def getDecklist(deckId):
	url = "https://api.moxfield.com/v2/decks/all/" + deckId
	print(f"Grabbing decklist <{deckId}>")
	r = requests.get(url)
	j = json.loads(r.text)
	return j


username = "thebear132"
userDecks = getUserDecks(username)
print("")
for e in userDecks["data"]:
	print(e["name"] + " "*(50-len(e["name"])) + e["publicUrl"])
#printJson(userDecks["data"][3])



print("Constructing the deck")
xDeck = ""
deckJson = getDecklist(userDecks["data"][3]["publicId"])
for card in deckJson["mainboard"]:
	c = deckJson["mainboard"][card]#["card"]
	cc = c["card"]
	
	quantity = c["quantity"]
	set = cc["set"].upper()
	setNr = cc["cn"]
	name = cc["name"]
	#1 [IKO:40] Anticipate
	line = f"{quantity} [{set}:{setNr}] {name}\n"
	xDeck += line

for card in deckJson["sideboard"]:
	c = deckJson["sideboard"][card]#["card"]
	cc = c["card"]
	
	quantity = c["quantity"]
	set = cc["set"].upper()
	setNr = cc["cn"]
	name = cc["name"]
	#SB: 1 [IKO:40] Anticipate
	line = f"SB: {quantity} [{set}:{setNr}] {name}\n"
	xDeck += line
print("XMage deck")
print(xDeck)
