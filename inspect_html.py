import requests
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "http://top250.info/charts/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Let's find the tables
    tables = soup.find_all('table')
    print(f"Total tables: {len(tables)}")
    
    # Print the first 2000 characters of the table HTML
    for idx, table in enumerate(tables):
        print(f"\n--- TABLE {idx} FIRST 3 ROWS HTML ---")
        rows = table.find_all('tr')
        print(f"Total rows in Table {idx}: {len(rows)}")
        for r_idx, row in enumerate(rows[:5]):
            print(f"Row {r_idx}: {str(row)[:400]}")
            
except Exception as e:
    print(f"Error: {e}")
