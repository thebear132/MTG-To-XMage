from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import json

firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
firefox_options.set_preference('devtools.jsonview.enabled', False)

driver = webdriver.Firefox(options=firefox_options)

print("Opening the URL...")
url = "https://api2.moxfield.com/v2/decks/search-sfw?showIllegal=true&authorUserNames=thebear132&pageNumber=1&pageSize=9999&sortType=updated&sortDirection=descending&board=mainboard"
old_url = "https://api.moxfield.com/v2/users/thebear132/decks?pageNumber=1&pageSize=99999"
driver.get(url)

print("Waiting for the page to load...")
time.sleep(1)

print("Fetching the raw response...")
raw_response = driver.execute_script("return document.body.innerText;")
print("Raw response fetched successfully!")
print(raw_response)
userDecks = json.loads(raw_response)["data"]
print(len(userDecks))

driver.quit()
print("Browser closed.")