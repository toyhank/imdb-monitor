import requests
import sys
from bs4 import BeautifulSoup
import re

sys.stdout.reconfigure(encoding='utf-8')

url = "http://top250.info/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Let's find all links on the page
    links = soup.find_all('a')
    print(f"Found {len(links)} total links on the page.")
    for idx, l in enumerate(links):
        print(f"Link {idx+1}: href='{l.get('href')}', text='{l.text.strip()}'")

            
except Exception as e:
    print(f"Error: {e}")
