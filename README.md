# MTG-To-XMage
A script to fetch your decks from Moxfield, MtgGoldfish, Archideckt and Tappedout to XMage `.dck` format ready to play!
When fetching from Moxfield, the version of the card is saved over to XMage.

### Usage
```
$ git clone https://github.com/thebear132/MTG-To-XMage
$ cd MTG-To-XMage
$ pip install -r requirements.txt --break-system-packages
$ python program.py -moxfield thebear132
```
When you have run the program once with your usernames, they will be saved in `config.json` for next time, so that any time in the future you only have to run ` $ python program.py` or double-click the  `.bat` or `.desktop` shortcuts.

### Help
```
bear@debian:~/Desktop/MTG-To-XMage$ python program.py --help
usage: program.py [-h] [-moxfield username] [-mtggoldfish username] [-archidekt username] [-tappedout username] [-o path]
                  [-v] [-vv]

MTG-To-Xmage | Download your online MTG decks to the XMage format

options:
  -h, --help            show this help message and exit
  -moxfield username    Your username for Moxfield
  -mtggoldfish username
                        Your username for MtgGoldfish
  -archidekt username   Your username for Archidekt
  -tappedout username   Your username for Tappedout
  -o path               Path to the folder to download your decks to
  -v                    Verbose mode
  -vv                   Super Verbose mode
```

### Issues
* ~~Currently Moxfield decks cant be downloaded due to them disallowed "scraping"...~~ (Has been fixed, works with Moxfield again!)


