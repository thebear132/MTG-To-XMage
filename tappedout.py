from utils import *

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
