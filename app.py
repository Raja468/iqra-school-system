from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "school_secret_key"


def get_db():
    conn = sqlite3.connect("school.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==================== LOGIN ====================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        user = db.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        db.close()
        if user:
            session["username"] = username
            session["role"] = user["role"]
            return redirect(f"/{user['role']}/dashboard")
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ==================== ADMIN DASHBOARD ====================
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    today = date.today().isoformat()
    total_students = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_teachers = db.execute("SELECT COUNT(*) FROM users WHERE role='teacher'").fetchone()[0]
    present_today  = db.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'", (today,)).fetchone()[0]
    fees_pending   = db.execute("SELECT COUNT(*) FROM fees WHERE status='unpaid'").fetchone()[0]
    recent_students = db.execute("SELECT id, name, roll_no, class_name FROM students ORDER BY id DESC LIMIT 5").fetchall()
    recent_notices  = db.execute("SELECT id, title, message, created_at FROM notices ORDER BY id DESC LIMIT 4").fetchall()
    db.close()
    return render_template("admin/dashboard.html",
        total_students=total_students,
        total_teachers=total_teachers,
        present_today=present_today,
        fees_pending=fees_pending,
        recent_students=recent_students,
        recent_notices=recent_notices
    )


# ==================== STUDENTS ====================
@app.route("/admin/students")
def admin_students():
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    students = db.execute("SELECT id, name, roll_no, class_name FROM students").fetchall()
    db.close()
    return render_template("admin/students.html", students=students)


@app.route("/admin/add_student", methods=["GET", "POST"])
def add_student():
    if session.get("role") != "admin":
        return redirect("/")
    if request.method == "POST":
        name       = request.form["name"]
        roll_no    = request.form["roll_no"]
        class_name = request.form["class_name"]
        username   = request.form["username"]
        password   = request.form["password"]
        db = get_db()
        try:
            db.execute("INSERT INTO students (name, roll_no, class_name) VALUES (?,?,?)", (name, roll_no, class_name))
            db.execute("INSERT INTO users (username, password, role) VALUES (?,?,'student')", (username, password))
            db.commit()
            db.close()
            return render_template("admin/add_student.html", success="Student added successfully!")
        except sqlite3.IntegrityError:
            db.close()
            return render_template("admin/add_student.html", error="Roll number or username already exists.")
    return render_template("admin/add_student.html")


@app.route("/admin/delete_student/<int:sid>")
def delete_student(sid):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (sid,))
    db.commit()
    db.close()
    return redirect("/admin/students")


# ==================== TEACHERS ====================
@app.route("/admin/teachers")
def admin_teachers():
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    teachers = db.execute("""
        SELECT t.id, t.name, t.email, t.subject, u.username
        FROM teachers t
        LEFT JOIN users u ON u.username = t.name
        WHERE u.role='teacher' OR u.role IS NULL
    """).fetchall()
    # fallback: get all teacher users
    if not teachers:
        teachers = db.execute("""
            SELECT u.id, u.username, '', '', u.username
            FROM users u WHERE u.role='teacher'
        """).fetchall()
    db.close()
    return render_template("admin/teachers.html", teachers=teachers)


@app.route("/admin/add_teacher", methods=["GET", "POST"])
def add_teacher():
    if session.get("role") != "admin":
        return redirect("/")
    if request.method == "POST":
        name     = request.form["name"]
        email    = request.form.get("email", "")
        subject  = request.form["subject"]
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        try:
            db.execute("INSERT INTO teachers (name, email, subject) VALUES (?,?,?)", (name, email, subject))
            db.execute("INSERT INTO users (username, password, role) VALUES (?,?,'teacher')", (username, password))
            db.commit()
            db.close()
            return render_template("admin/add_teacher.html", success="Teacher added successfully!")
        except sqlite3.IntegrityError:
            db.close()
            return render_template("admin/add_teacher.html", error="Username or email already exists.")
    return render_template("admin/add_teacher.html")


@app.route("/admin/delete_teacher/<int:tid>")
def delete_teacher(tid):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM teachers WHERE id=?", (tid,))
    db.commit()
    db.close()
    return redirect("/admin/teachers")


# ==================== ATTENDANCE (ADMIN) ====================
@app.route("/admin/attendance", methods=["GET", "POST"])
def admin_attendance():
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    students = db.execute("SELECT id, name, roll_no, class_name FROM students").fetchall()
    today = date.today().isoformat()
    if request.method == "POST":
        for s in students:
            status = request.form.get(str(s["id"]))
            if status:
                db.execute("""
                    INSERT OR REPLACE INTO attendance (student_id, date, status)
                    VALUES (?,?,?)
                """, (s["id"], today, status))
        db.commit()
        db.close()
        return render_template("admin/attendance.html", students=students, today=today, success="Attendance saved!")
    db.close()
    return render_template("admin/attendance.html", students=students, today=today)


@app.route("/admin/view_attendance", methods=["GET", "POST"])
def view_attendance():
    if session.get("role") != "admin":
        return redirect("/")
    records = []
    selected_date = None
    if request.method == "POST":
        selected_date = request.form["date"]
        db = get_db()
        records = db.execute("""
            SELECT s.name, a.status FROM attendance a
            JOIN students s ON s.id = a.student_id
            WHERE a.date=? ORDER BY s.name
        """, (selected_date,)).fetchall()
        db.close()
    return render_template("admin/view_attendance.html", records=records, selected_date=selected_date)


# ==================== NOTICES ====================
@app.route("/admin/notices", methods=["GET", "POST"])
def admin_notices():
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    if request.method == "POST":
        db.execute("INSERT INTO notices (title, message) VALUES (?,?)",
                   (request.form["title"], request.form["message"]))
        db.commit()
        notices = db.execute("SELECT id, title, message, created_at FROM notices ORDER BY id DESC").fetchall()
        db.close()
        return render_template("admin/notices.html", notices=notices, success="Notice posted!")
    notices = db.execute("SELECT id, title, message, created_at FROM notices ORDER BY id DESC").fetchall()
    db.close()
    return render_template("admin/notices.html", notices=notices)


@app.route("/admin/delete_notice/<int:nid>")
def delete_notice(nid):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("DELETE FROM notices WHERE id=?", (nid,))
    db.commit()
    db.close()
    return redirect("/admin/notices")


# ==================== FEE SYSTEM ====================
@app.route("/admin/fees")
def admin_fees():
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    current_month = date.today().strftime("%B")
    current_year  = date.today().year
    fees = db.execute("""
        SELECT f.id, s.name, s.class_name, f.month, f.year, f.status, f.paid_date
        FROM fees f JOIN students s ON s.id = f.student_id
        WHERE f.year=? ORDER BY s.name
    """, (current_year,)).fetchall()
    paid_count   = sum(1 for f in fees if f["status"] == "paid")
    unpaid_count = sum(1 for f in fees if f["status"] != "paid")
    total_students = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    db.close()
    return render_template("admin/fees.html",
        fees=fees, paid_count=paid_count, unpaid_count=unpaid_count,
        total_students=total_students, current_month=current_month
    )


@app.route("/admin/fees/generate", methods=["POST"])
def generate_fees():
    if session.get("role") != "admin":
        return redirect("/")
    month = request.form["month"]
    year  = int(request.form["year"])
    db = get_db()
    students = db.execute("SELECT id FROM students").fetchall()
    for s in students:
        db.execute("""
            INSERT OR IGNORE INTO fees (student_id, month, year, amount, status)
            VALUES (?,?,?,2000,'unpaid')
        """, (s["id"], month, year))
    db.commit()
    db.close()
    return redirect("/admin/fees")


@app.route("/admin/fees/pay/<int:fid>")
def mark_fee_paid(fid):
    if session.get("role") != "admin":
        return redirect("/")
    db = get_db()
    db.execute("UPDATE fees SET status='paid', paid_date=? WHERE id=?",
               (date.today().isoformat(), fid))
    db.commit()
    db.close()
    return redirect("/admin/fees")


# ==================== TEACHER ====================
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    db = get_db()
    notices = db.execute("SELECT title, message, created_at FROM notices ORDER BY id DESC LIMIT 5").fetchall()
    db.close()
    return render_template("teacher/dashboard.html", notices=notices)


@app.route("/teacher/attendance", methods=["GET", "POST"])
def teacher_attendance():
    if session.get("role") != "teacher":
        return redirect("/")
    db = get_db()
    students = db.execute("SELECT id, name FROM students").fetchall()
    today = date.today().isoformat()
    if request.method == "POST":
        for s in students:
            status = request.form.get(str(s["id"]))
            if status:
                db.execute("""
                    INSERT OR REPLACE INTO attendance (student_id, date, status)
                    VALUES (?,?,?)
                """, (s["id"], today, status))
        db.commit()
        db.close()
        return render_template("teacher/attendance.html", students=students, today=today, success="Attendance saved!")
    db.close()
    return render_template("teacher/attendance.html", students=students, today=today)


@app.route("/teacher/notices")
def teacher_notices():
    if session.get("role") != "teacher":
        return redirect("/")
    db = get_db()
    notices = db.execute("SELECT title, message, created_at FROM notices ORDER BY id DESC").fetchall()
    db.close()
    return render_template("teacher/notices.html", notices=notices)


# ==================== STUDENT ====================
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")
    username = session["username"]
    db = get_db()
    student = db.execute("SELECT id FROM students WHERE roll_no=?", (username,)).fetchone()
    attendance = []
    if student:
        attendance = db.execute("""
            SELECT date, status FROM attendance
            WHERE student_id=? ORDER BY date DESC
        """, (student["id"],)).fetchall()
    notices = db.execute("SELECT title, message, created_at FROM notices ORDER BY id DESC").fetchall()
    db.close()
    return render_template("student/dashboard.html", attendance=attendance, notices=notices)


@app.route("/student/notices")
def student_notices():
    if session.get("role") != "student":
        return redirect("/")
    db = get_db()
    notices = db.execute("SELECT title, message, created_at FROM notices ORDER BY id DESC").fetchall()
    db.close()
    return render_template("student/notices.html", notices=notices)


# ==================== RUN ====================
if __name__ == "__main__":
    app.run(debug=True)
