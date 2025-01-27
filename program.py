import argparse
from tokenize import String
import json
import logging
import os

from utils import *
from moxfield import MoxField
from mtggoldfish import MtgGoldfish
from archideckt import Archidekt
from tappedout import Tappedout


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
