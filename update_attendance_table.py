import sqlite3

db = sqlite3.connect("school.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT,
    UNIQUE(student_id, date)
)
""")

db.commit()
db.close()

print("Attendance table updated successfully")
