from utils import *
import requests


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

    def __getDecklist(self, deckUrl):
        url = f"https://www.mtggoldfish.com{deckUrl}#paper"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.",
        }  # MTGGoldfish gives a 406 if the Accept header is not set properly
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            logResponse("__getDecklist.log", r)
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

            deckList = self.__getDecklist(userDecks[deckName])
            xDeck = convertDeckToXmage(deckList)
            writeXmageToPath(self.xmageFolderPath, deckName,
                             deckList["format"], xDeck)

        #deckList = self.__getDecklist("Malcolm/Breeches", "/deck/4754316")
        #deckList = self.__getDecklist("Arcades EDH Aggro", "/deck/1430191")
