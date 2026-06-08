import sys
# Set output encoding
sys.stdout.reconfigure(encoding='utf-8')

try:
    from scraper import IMDBScraper
    s = IMDBScraper()
    movies = s.fetch_top250()
    print(f"Parsed total movies: {len(movies)}")
    
    if len(movies) >= 3:
        print("First 3 movies parsed:")
        for m in movies[:3]:
            print(f"  {m}")
            
    # Run validation
    is_valid = s.validate_data(movies)
    print(f"Validation result: {is_valid}")
    
except Exception as e:
    print(f"Error occurred: {e}")
    sys.exit(1)
