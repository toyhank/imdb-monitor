from curl_cffi import requests
from bs4 import BeautifulSoup

url = "https://www.imdb.com/chart/top/"
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

print("Requesting via curl_cffi with chrome impersonation...")
r = requests.get(url, headers=headers, impersonate="chrome", timeout=30)
print(f"Status Code: {r.status_code}")
print(f"Content Length: {len(r.content)} bytes")

soup = BeautifulSoup(r.content, 'html.parser')
title = soup.title.string if soup.title else "No Title"
print(f"Page Title: {title}")

# Check if challenge is present
is_challenge = "challenge" in r.text or "awswaf" in r.text or "verify that you're not a robot" in r.text
print(f"Is WAF Challenge Page? {is_challenge}")

# Let's count some elements
items = soup.find_all('li', class_='ipc-metadata-list-summary-item')
print(f"Found 'ipc-metadata-list-summary-item' elements: {len(items)}")

# Let's also check for json-ld
json_scripts = soup.find_all('script', type='application/ld+json')
print(f"Found application/ld+json scripts: {len(json_scripts)}")
for idx, script in enumerate(json_scripts):
    try:
        import json
        data = json.loads(script.string)
        print(f"  Script {idx} Type: {data.get('@type')}")
    except Exception as e:
        print(f"  Script {idx} parsing failed: {e}")
