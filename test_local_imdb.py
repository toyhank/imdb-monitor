import requests
from bs4 import BeautifulSoup
import re

url = "https://www.imdb.com/chart/top/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

print(f"Requesting {url} from local machine...")
try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    print(f"Page Title: {title}")
    
    # Check for robot check/challenge
    is_challenge = "challenge" in response.text or "awswaf" in response.text or "verify that you're not a robot" in response.text
    print(f"Is WAF Challenge Page? {is_challenge}")
    
    # Check elements
    movie_containers = soup.find_all('li', class_='ipc-metadata-list-summary-item')
    print(f"Found 'ipc-metadata-list-summary-item' elements: {len(movie_containers)}")
    
    # Try old format
    old_containers = soup.find_all('tr', class_='titleColumn')
    print(f"Found 'tr.titleColumn' elements: {len(old_containers)}")
    
    # JSON-LD scripts
    json_scripts = soup.find_all('script', type='application/ld+json')
    print(f"Found application/ld+json scripts: {len(json_scripts)}")
    
except Exception as e:
    print(f"Error occurred: {e}")
