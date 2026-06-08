import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://www.imdb.com/chart/top/"
print("Launching playwright sync...")

try:
    with sync_playwright() as p:
        print("Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        print("Creating context and page...")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {url}...")
        response = page.goto(url, timeout=60000)
        
        print(f"Response status: {response.status if response else 'No Response'}")
        
        # Wait a bit for JS challenges or rendering
        page.wait_for_timeout(5000)
        
        content = page.content()
        print(f"Content length: {len(content)} bytes")
        
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.title.string if soup.title else "No Title"
        print(f"Page Title: {title}")
        
        is_challenge = "challenge" in content.lower() or "verify that you're not a robot" in content.lower()
        print(f"Is WAF Challenge Page? {is_challenge}")
        
        # Find movie containers
        items = soup.find_all('li', class_='ipc-metadata-list-summary-item')
        print(f"Found 'ipc-metadata-list-summary-item' elements: {len(items)}")
        
        # Close browser
        browser.close()
        print("Browser closed.")
        
except Exception as e:
    print(f"Error occurred: {e}", file=sys.stderr)
    sys.exit(1)
