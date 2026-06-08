import requests
import json

url = "https://raw.githubusercontent.com/movie-monk-b0t/top250/main/top250.json"
response = requests.get(url)
data = response.json()

for i, item in enumerate(data):
    if "Shawshank" in item.get('name', ''):
        print(f"Index in JSON: {i}")
        print(json.dumps(item, indent=2))
        break
