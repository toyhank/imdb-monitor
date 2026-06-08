import requests

api_key = "7e68224382e3733c65326d529bea6714"
imdb_id = "tt0111161"
url = f"https://api.themoviedb.org/3/find/{imdb_id}"

params = {
    'api_key': api_key,
    'external_source': 'imdb_id',
    'language': 'zh-CN'
}

print(f"Testing TMDB API for {imdb_id}...")
try:
    response = requests.get(url, params=params, timeout=15)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        movie_results = data.get('movie_results', [])
        if movie_results:
            movie = movie_results[0]
            print("Success! Movie found in TMDB:")
            # Use ascii-friendly characters and print
            print(f"  Title (CN): {movie.get('title')}".encode('utf-8', errors='replace').decode('gbk', errors='replace'))
            print(f"  Original Title: {movie.get('original_title')}".encode('utf-8', errors='replace').decode('gbk', errors='replace'))
            print(f"  Release Date: {movie.get('release_date')}")
        else:
            print("Movie not found in TMDB.")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error occurred: {e}")
