import requests
import json
import re

url = "https://raw.githubusercontent.com/movie-monk-b0t/top250/main/top250.json"
print("Fetching:", url)
response = requests.get(url)
data = response.json()

print("Root type:", type(data))
print("Length:", len(data))

if isinstance(data, list) and len(data) > 0:
    first = data[0]
    print("\nFirst item keys:", list(first.keys()))
    print("\nFirst item details (non-nested):")
    for k, v in first.items():
        if not isinstance(v, (dict, list)):
            print(f"  {k}: {v}")
    
    print("\nFirst item nested structures keys:")
    for k, v in first.items():
        if isinstance(v, dict):
            print(f"  {k} (dict): {list(v.keys())}")
        elif isinstance(v, list):
            print(f"  {k} (list of {type(v[0]).__name__ if v else 'empty'}): length {len(v)}")

    # Let's see if we can parse it using similar logic to _parse_json_ld
    print("\nSimulating parsing of first 3 items:")
    for i, item in enumerate(data[:3], 1):
        title = item.get('name', '')
        url = item.get('url', '')
        imdb_id = None
        if url:
            id_match = re.search(r'/title/(tt\d+)/', url)
            if id_match:
                imdb_id = id_match.group(1)
        
        # rating
        rating = None
        aggregate_rating = item.get('aggregateRating', {})
        if aggregate_rating:
            rating = aggregate_rating.get('ratingValue')
        
        print(f"Rank: {i}, Title: {title}, IMDB ID: {imdb_id}, Rating: {rating}")
