import sys
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://www.imdb.com/chart/top/"
print("Launching playwright sync...")

try:
    with sync_playwright() as p:
        print("Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        print("Creating context with English locale...")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = context.new_page()
        
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        
        print("Waiting for initial list load...")
        page.wait_for_selector('li.ipc-metadata-list-summary-item', timeout=20000)
        
        print("Scrolling down to load all 250 movies...")
        # Scroll down in increments to trigger lazy loading
        for i in range(10):
            page.evaluate("window.scrollBy(0, 2000)")
            time.sleep(1.0)
        
        # Scroll to the absolute bottom just in case
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2.0)
        
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        items = soup.find_all('li', class_='ipc-metadata-list-summary-item')
        print(f"Total 'ipc-metadata-list-summary-item' elements found: {len(items)}")
        
        if len(items) > 0:
            print("\nFirst 5 movies:")
            for idx, item in enumerate(items[:5], 1):
                print(f"  {idx}. {item.get_text(strip=True)[:100]}")
                
            print("\nLast 5 movies:")
            for idx, item in enumerate(items[-5:], len(items) - 4):
                print(f"  {idx}. {item.get_text(strip=True)[:100]}")
        
        # Close browser
        browser.close()
        print("Browser closed.")
        
except Exception as e:
    print(f"Error occurred: {e}", file=sys.stderr)
    sys.exit(1)
