import requests
import json
import logging, sys

"""Messing around with the Moxfield API

All decks
https://api.moxfield.com/v2/decks/all?pageNumber=1&pageSize=10




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


username = "thebear132"
userDecks = getUserDecks(username)
print("")
for e in userDecks["data"]:
	print(e["name"] + " "*(50-len(e["name"])) + e["publicUrl"])


