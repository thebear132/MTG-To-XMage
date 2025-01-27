from utils import *

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
