import requests
import sys

# Set stdout to utf-8 to avoid encoding issues on Windows
sys.stdout.reconfigure(encoding='utf-8')

url = "https://raw.githubusercontent.com/behzadkazemi/imdb-top-250/master/List.json"
try:
    print(f"Fetching from {url}...")
    response = requests.get(url, timeout=10)
    data = response.json()
    print(f"Total movies: {len(data)}")
    print("First 15 movies in the JSON file:")
    for i in range(min(15, len(data))):
        item = data[i]
        # print keys and some info
        print(f"  {i+1}. {item.get('name') or item.get('title')} (Rank: {item.get('rank')}, URL: {item.get('url') or item.get('id')})")
except Exception as e:
    print(f"Error: {e}")

