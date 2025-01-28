import json
import subprocess
from playwright.sync_api import sync_playwright

# Install Firefox driver automatically
subprocess.run(["playwright", "install", "firefox"], check=True)

p = sync_playwright().start()
browser = p.firefox.launch()

page = browser.new_page()
page.goto("https://api.moxfield.com/v2/users/thebear132/decks?pageNumber=1&pageSize=1")
page.goto("https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw")
# print(page.inner_html("pre"))
j = json.loads(page.inner_html("pre"))
browser.close()
p.stop()

print(j)

