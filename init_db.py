import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    noise_type TEXT,
    db_level INTEGER,
    location TEXT,
    description TEXT,
    status TEXT,
    evidence TEXT,
    date TEXT
)
""")

conn.commit()
conn.close()
print("Database initialized")
