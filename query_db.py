import sqlite3

db_path = "/IMDB/Augment/imdb_top250.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]
print("Tables in database:", tables)

# Get row counts
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"Table '{table}' row count: {count}")

# Get latest snapshot date
if 'snapshots' in tables:
    cursor.execute("SELECT MAX(created_at) FROM snapshots")
    max_snapshot = cursor.fetchone()[0]
    print(f"Latest snapshot date: {max_snapshot}")
else:
    # Maybe snapshots is not the name, let's look at schema of tables
    pass

# Print recent changes
if 'changes' in tables:
    print("\nRecent 10 changes in database:")
    cursor.execute("PRAGMA table_info(changes)")
    cols = [c[1] for c in cursor.fetchall()]
    cursor.execute("SELECT * FROM changes ORDER BY change_date DESC LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        print(dict(zip(cols, row)))

conn.close()
