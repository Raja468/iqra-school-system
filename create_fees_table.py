"""Create the fees table in school.db"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "school.db")
db = sqlite3.connect(DB_PATH)
db.execute("""
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        month TEXT NOT NULL,
        year INTEGER NOT NULL,
        status TEXT DEFAULT 'unpaid',
        paid_date TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
""")
db.commit()
print("fees table created/verified.")
# Show tables
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
db.close()