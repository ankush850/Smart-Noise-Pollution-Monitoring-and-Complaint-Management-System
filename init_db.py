import sqlite3
from werkzeug.security import generate_password_hash
import os

DB_PATH = "database.db"

# Delete existing DB if it exists for a fresh start in this case
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Create Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)
""")

# Create Complaints table
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
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# Add an admin user
admin_name = "System Admin"
admin_email = "admin@noisewatch.com"
admin_pass = generate_password_hash("admin123")
cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
            (admin_name, admin_email, admin_pass, "admin"))

# Add a standard user
user_name = "John Doe"
user_email = "john@example.com"
user_pass = generate_password_hash("user123")
cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
            (user_name, user_email, user_pass, "user"))

# Add sample complaints
cur.execute("""
INSERT INTO complaints (user_id, noise_type, db_level, location, description, status, evidence, date) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (2, "Construction", 90, "Downtown Main St", "Jackhammering starting at 6 AM every day.", "Pending", "", "2026-01-27 08:30"))

conn.commit()
conn.close()
print("Database initialized with admin and sample data.")
