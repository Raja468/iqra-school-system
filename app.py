from flask import Flask, render_template, request, redirect, session
import psycopg2
import psycopg2.extras
from datetime import date
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "school_secret_key")


# ================= DATABASE =================
def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode="require")
    return conn


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        db.close()

        if user:
            session["username"] = username
            session["role"] = user[0]

            if user[0] == "admin":
                return redirect("/admin/dashboard")
            elif user[0] == "teacher":
                return redirect("/teacher/dashboard")
            elif user[0] == "student":
                return redirect("/student/dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= ADMIN =================
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")
    return render_template("admin/dashboard.html")


@app.route("/admin/teachers")
def admin_teachers():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, username
        FROM users
        WHERE role='teacher'
    """)
    teachers = cursor.fetchall()
    db.close()

    return render_template("admin/teachers.html", teachers=teachers)


@app.route("/admin/students")
def admin_students():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, name, roll_no, class_name
        FROM students
    """)
    students = cursor.fetchall()
    db.close()

    return render_template("admin/students.html", students=students)


@app.route("/admin/add_student", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        class_name = request.form["class_name"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO students (name, roll_no, class_name)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (name, roll_no, class_name))
        db.commit()
        db.close()
        return redirect("/admin/students")

    return render_template("admin/add_student.html")


@app.route("/admin/add_teacher", methods=["GET", "POST"])
def add_teacher():
    if session.get("role") != "admin":
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, 'teacher')
            ON CONFLICT DO NOTHING
        """, (username, password))
        db.commit()
        db.close()
        return redirect("/admin/teachers")

    return render_template("admin/add_teacher.html")


@app.route("/admin/notices", methods=["GET", "POST"])
def admin_notices():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        title = request.form["title"]
        message = request.form["message"]
        cursor.execute("""
            INSERT INTO notices (title, message)
            VALUES (%s, %s)
        """, (title, message))
        db.commit()

    cursor.execute("""
        SELECT title, message, created_at
        FROM notices
        ORDER BY id DESC
    """)
    notices = cursor.fetchall()
    db.close()

    return render_template("admin/notices.html", notices=notices)


@app.route("/admin/attendance")
def admin_attendance():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.name, a.date, a.status
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        ORDER BY a.date DESC
    """)
    records = cursor.fetchall()
    db.close()

    return render_template("admin/view_attendance.html", records=records)


# ================= TEACHER =================
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    return render_template("teacher/dashboard.html")


@app.route("/teacher/attendance", methods=["GET", "POST"])
def teacher_attendance():
    if session.get("role") != "teacher":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    if request.method == "POST":
        today = date.today().isoformat()

        for student in students:
            student_id = student[0]
            status = request.form.get(str(student_id))

            if status:
                cursor.execute("""
                    INSERT INTO attendance (student_id, date, status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (student_id, date) DO NOTHING
                """, (student_id, today, status))

        db.commit()
        db.close()
        return redirect("/teacher/dashboard")

    db.close()
    return render_template("teacher/attendance.html", students=students)


# ================= STUDENT =================
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")

    username = session["username"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM students WHERE roll_no=%s", (username,))
    student = cursor.fetchone()

    attendance = []
    notices = []

    if student:
        cursor.execute("""
            SELECT date, status
            FROM attendance
            WHERE student_id=%s
            ORDER BY date DESC
        """, (student[0],))
        attendance = cursor.fetchall()

    cursor.execute("""
        SELECT title, message, created_at
        FROM notices
        ORDER BY id DESC
    """)
    notices = cursor.fetchall()

    db.close()

    return render_template(
        "student/dashboard.html",
        attendance=attendance,
        notices=notices
    )


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=False)