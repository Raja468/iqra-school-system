import sqlite3

db = sqlite3.connect("school.db")
cursor = db.cursor()

# ---------------- USERS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Default admin
cursor.execute("""
INSERT OR IGNORE INTO users (username, password, role)
VALUES ('admin', 'admin123', 'admin')
""")

# ---------------- STUDENTS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    class_name TEXT NOT NULL
)
""")

# ---------------- TEACHERS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    subject TEXT NOT NULL
)
""")

# ---------------- ATTENDANCE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT NOT NULL,
    UNIQUE(student_id, date),
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")

# ---------------- NOTICES ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------------- FEES (NEW) ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT DEFAULT 'unpaid',
    paid_date TEXT,
    UNIQUE(student_id, month, year),
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")

db.commit()
db.close()

print("✅ Database & tables created successfully")
