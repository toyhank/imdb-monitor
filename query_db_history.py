import sqlite3

db_path = "/IMDB/Augment/imdb_top250.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check movie_history structure
cursor.execute("PRAGMA table_info(movie_history)")
cols = [c[1] for c in cursor.fetchall()]
print("movie_history columns:", cols)

# Query recent records in movie_history
cursor.execute("SELECT DISTINCT created_at FROM movie_history ORDER BY created_at DESC LIMIT 10")
dates = [r[0] for r in cursor.fetchall()]
print("Distinct created_at dates in movie_history:", dates)

# Check what was recorded on 2026-03-19
cursor.execute("SELECT * FROM movie_history WHERE created_at LIKE '2026-03-19%' LIMIT 3")
rows = cursor.fetchall()
print("\nSample rows from 2026-03-19 in movie_history:")
for r in rows:
    print(dict(zip(cols, r)))

conn.close()
