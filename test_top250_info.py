import requests
import sys
from bs4 import BeautifulSoup

# Set stdout to utf-8 to avoid encoding issues on Windows
sys.stdout.reconfigure(encoding='utf-8')

url = "http://top250.info/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

print(f"Requesting {url}...")
try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes")
    
    # Check if there is some text in response
    soup = BeautifulSoup(response.content, 'html.parser')
    print(f"Title of page: {soup.title.string if soup.title else 'No title'}")
    
    # Print first 500 characters of text to see structure
    print("\nPage preview:")
    print(response.text[:1000])
except Exception as e:
    print(f"Error occurred: {e}")
