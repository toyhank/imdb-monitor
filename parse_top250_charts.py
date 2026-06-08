import requests
import sys
from bs4 import BeautifulSoup
import re

sys.stdout.reconfigure(encoding='utf-8')

url = "http://top250.info/charts/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

try:
    print(f"Requesting {url}...")
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Let's inspect the page tables to see where the movies are listed
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on the charts page.")
    
    # Find all links that look like "/movie/?\d+"
    movie_links = soup.find_all('a', href=re.compile(r'^/movie/\?\d+$'))
    print(f"Found {len(movie_links)} links matching '/movie/?<id>' pattern.")
    
    # Let's see some details
    movies = []
    seen_ids = set()
    for link in movie_links:
        href = link.get('href')
        imdb_num = href.split('?')[1]
        imdb_id = f"tt{imdb_num.zfill(7)}"
        title = link.text.strip()
        if not title:
            continue
        if imdb_id not in seen_ids:
            seen_ids.add(imdb_id)
            movies.append((imdb_id, title))
            
    print(f"Unique movies extracted: {len(movies)}")
    print("First 10 movies:")
    for idx, (imdb_id, title) in enumerate(movies[:10], 1):
        print(f"  {idx}. ID: {imdb_id}, Title: {title}")
        
    print("\nLast 5 movies:")
    for idx, (imdb_id, title) in enumerate(movies[-5:], len(movies) - 4):
        print(f"  {idx}. ID: {imdb_id}, Title: {title}")
        
except Exception as e:
    print(f"Error: {e}")
