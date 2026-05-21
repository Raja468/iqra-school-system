import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
print("DATABASE_URL =", os.environ.get("DATABASE_URL"))
DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

# ================= USERS =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# ================= STUDENTS =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    class_name TEXT NOT NULL
)
""")

# ================= ATTENDANCE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status TEXT NOT NULL,
    UNIQUE(student_id, date)
)
""")

# ================= NOTICES =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS notices (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ================= DEFAULT ADMIN =================
cursor.execute("""
INSERT INTO users (username, password, role)
VALUES (%s, %s, %s)
ON CONFLICT (username) DO NOTHING
""", ("admin", "admin123", "admin"))

conn.commit()
conn.close()

print("Database and tables created successfully!")