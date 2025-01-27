import asyncio
from pyppeteer import launch
import json

async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

    print("Opening the URL...")
    url = "https://api2.moxfield.com/v2/decks/search-sfw?authorUserNames=thebear132&pageNumber=1&pageSize=9999&sortType=updated"
    url = "https://api.moxfield.com/v2/users/thebear132/decks?pageNumber=1&pageSize=99999"
    await page.goto(url)

    print("Fetching the raw response...")
    raw_response = await page.evaluate('document.body.innerText')
    print("Raw response fetched successfully!")
    print(raw_response)
    userDecks = json.loads(raw_response)["data"]
    print(len(userDecks))

    await browser.close()
    print("Browser closed.")

asyncio.get_event_loop().run_until_complete(main())
