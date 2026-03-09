import sqlite3

db = sqlite3.connect("school.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    subject TEXT
)
""")

db.commit()
db.close()

print("Teachers table created")
