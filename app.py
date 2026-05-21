from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "school_secret_key")
DB_PATH = os.path.join(os.path.dirname(__file__), "school.db")


# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
            "SELECT role FROM users WHERE username=? AND password=?",
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

    db = get_db()
    cursor = db.cursor()

    # Counts
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
    total_teachers = cursor.fetchone()[0]

    # Present today
    from datetime import date
    today = date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'", (today,))
    present_today = cursor.fetchone()[0]

    # Fees pending this month
    from datetime import datetime
    current_month = datetime.now().strftime("%B")
    cursor.execute("SELECT COUNT(*) FROM fees WHERE month=? AND year=? AND status='unpaid'",
                   (current_month, datetime.now().year))
    fees_pending = cursor.fetchone()[0]

    # Recent students (last 5)
    cursor.execute("SELECT name, roll_no, class_name FROM students ORDER BY id DESC LIMIT 5")
    recent_students = cursor.fetchall()

    # Latest notices (last 5)
    cursor.execute("SELECT title, message, created_at FROM notices ORDER BY id DESC LIMIT 5")
    latest_notices = cursor.fetchall()

    db.close()

    return render_template("admin/dashboard.html",
                           total_students=total_students,
                           total_teachers=total_teachers,
                           present_today=present_today,
                           fees_pending=fees_pending,
                           recent_students=recent_students,
                           latest_notices=latest_notices)


@app.route("/admin/teachers")
def admin_teachers():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role='teacher'")
    teachers_data = cursor.fetchall()

    # Build richer teacher data: [id, name, subject, class, username]
    teachers = []
    for t in teachers_data:
        teachers.append((t[0], t[1], t[1], "General", t[1]))
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

    error = None
    success = None

    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        class_name = request.form["class_name"]
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO students (name, roll_no, class_name)
                VALUES (?, ?, ?)
            """, (name, roll_no, class_name))

            if username and password:
                cursor.execute("""
                    INSERT OR IGNORE INTO users (username, password, role)
                    VALUES (?, ?, 'student')
                """, (username, password))

            db.commit()
            success = f"Student '{name}' added successfully."
        except Exception as e:
            db.rollback()
            error = f"Error: {str(e)}"
        db.close()

        if not error:
            return redirect("/admin/students")

    return render_template("admin/add_student.html", error=error, success=success)


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
            VALUES (?, ?, 'teacher')
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
            VALUES (?, ?)
        """, (title, message))
        db.commit()

    cursor.execute("""
        SELECT id, title, message, created_at
        FROM notices
        ORDER BY id DESC
    """)
    notices = cursor.fetchall()
    db.close()

    return render_template("admin/notices.html", notices=notices)


@app.route("/admin/attendance", methods=["GET", "POST"])
def admin_attendance():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    selected_date = None
    query = """
        SELECT s.name, a.date, a.status
        FROM attendance a
        JOIN students s ON s.id = a.student_id
    """

    if request.method == "POST":
        selected_date = request.form.get("date")
        query += " WHERE a.date=? ORDER BY a.date DESC, s.name ASC"
        records = cursor.execute(query, (selected_date,)).fetchall()
    else:
        query += " ORDER BY a.date DESC"
        records = cursor.execute(query).fetchall()

    db.close()
    return render_template("admin/view_attendance.html", records=records, selected_date=selected_date)


# ================= DELETE ROUTES =================
@app.route("/admin/delete_student/<int:student_id>")
def delete_student(student_id):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (student_id,))
    db.commit()
    db.close()
    return redirect("/admin/students")


@app.route("/admin/delete_teacher/<int:teacher_id>")
def delete_teacher(teacher_id):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM users WHERE id=? AND role='teacher'", (teacher_id,))
    db.commit()
    db.close()
    return redirect("/admin/teachers")


@app.route("/admin/delete_notice/<int:notice_id>")
def delete_notice(notice_id):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM notices WHERE id=?", (notice_id,))
    db.commit()
    db.close()
    return redirect("/admin/notices")


# ================= FEES =================
@app.route("/admin/fees")
def admin_fees():
    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, roll_no, class_name FROM students")
    students = cursor.fetchall()

    # Determine current month/year
    from datetime import datetime
    now = datetime.now()
    current_month = now.strftime("%B")
    current_year = now.year

    cursor.execute("""
        SELECT f.id, s.name, s.class_name, f.month, f.year, f.status, f.paid_date
        FROM fees f
        JOIN students s ON s.id = f.student_id
        ORDER BY f.year DESC,
            CASE f.month
                WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
                WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
                WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9
                WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
            END DESC
    """)
    fees = cursor.fetchall()

    paid_count = sum(1 for f in fees if f[5] == 'paid')
    unpaid_count = sum(1 for f in fees if f[5] != 'paid')
    total_students = len(students)

    db.close()

    return render_template(
        "admin/fees.html",
        fees=fees,
        paid_count=paid_count,
        unpaid_count=unpaid_count,
        total_students=len(students),
        current_month=current_month
    )


@app.route("/admin/fees/generate", methods=["POST"])
def generate_fees():
    if session.get("role") != "admin":
        return redirect("/")

    month = request.form["month"]
    year = int(request.form["year"])

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM students")
    students = cursor.fetchall()

    for s in students:
        cursor.execute("""
            INSERT OR IGNORE INTO fees (student_id, month, year, status)
            VALUES (?, ?, ?, 'unpaid')
        """, (s[0], month, year))

    db.commit()
    db.close()
    return redirect("/admin/fees")


@app.route("/admin/fees/pay/<int:fee_id>")
def pay_fee(fee_id):
    if session.get("role") != "admin":
        return redirect("/")

    from datetime import date
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE fees SET status='paid', paid_date=?
        WHERE id=? AND status='unpaid'
    """, (date.today().isoformat(), fee_id))
    db.commit()
    db.close()
    return redirect("/admin/fees")


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
                    VALUES (?, ?, ?)
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

    cursor.execute("SELECT id FROM students WHERE roll_no=?", (username,))
    student = cursor.fetchone()

    attendance = []
    notices = []

    if student:
        cursor.execute("""
            SELECT date, status
            FROM attendance
            WHERE student_id=?
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