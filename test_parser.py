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
    print(f"Fetching from {url}...")
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # We want table 1, which has 251 rows
    tables = soup.find_all('table')
    if len(tables) < 2:
        print("Error: Could not find the movie list table.")
        sys.exit(1)
        
    table = tables[1]
    rows = table.find_all('tr')[1:] # Skip header
    
    movies = []
    for idx, row in enumerate(rows, 1):
        cols = row.find_all('td')
        if len(cols) < 5:
            print(f"Skipping row {idx} due to unexpected structure: {row}")
            continue
            
        # 1. Rank
        rank = int(cols[0].text.strip())
        
        # 2. Movie link & Title/Year info
        link_elem = cols[2].find('a')
        if not link_elem:
            print(f"Skipping row {idx}: No link element found.")
            continue
            
        href = link_elem.get('href', '')
        # Extract ID
        id_match = re.search(r'\?(\d+)', href)
        if not id_match:
            print(f"Skipping row {idx}: Invalid link href format: {href}")
            continue
            
        imdb_num = id_match.group(1)
        imdb_id = f"tt{imdb_num.zfill(7)}"
        
        # Title and Year
        full_text = link_elem.text.strip()
        text_match = re.search(r'^(.*?)\s*\((\d{4})\)$', full_text)
        if text_match:
            title = text_match.group(1).strip()
            year = int(text_match.group(2))
        else:
            title = full_text
            year = None
            
        # 3. Rating
        try:
            rating = float(cols[3].text.strip())
        except ValueError:
            rating = None
            
        movies.append({
            'rank': rank,
            'title': title,
            'year': year,
            'rating': rating,
            'imdb_id': imdb_id
        })
        
    print(f"Successfully parsed {len(movies)} movies.")
    print("First 3 movies:")
    for m in movies[:3]:
        print(f"  {m}")
    print("Last 3 movies:")
    for m in movies[-3:]:
        print(f"  {m}")
        
except Exception as e:
    print(f"Error occurred: {e}")
