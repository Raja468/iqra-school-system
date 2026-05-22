# School Management System

A Flask-based school management application that supports **admin**, **teacher**, and **student** roles with core features like authentication, student/teacher management, attendance tracking, fee tracking, and notices.

> Note: The running application (`app.py`) uses a local **SQLite** database file named `school.db`.

---

## Features

### Admin
- View dashboard metrics (students, teachers, today’s attendance, pending fees)
- Manage students
- Manage teachers
- Create and delete notices
- Mark/view attendance for any date (admin view)
- Generate fees for all students for a selected month/year
- Mark fees as paid

### Teacher
- Mark attendance for students for the selected day (via teacher attendance page)

### Student
- View personal attendance history
- View school notices

---

## Tech Stack
- **Backend:** Flask (Gunicorn for production)
- **Database:** SQLite (runtime via `school.db`)
- **Templating:** Jinja2
- **Frontend:** HTML templates + static CSS/JS

---

## Prerequisites
- Python 3.9+ recommended
- pip

---

## Setup (Local)

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Create database tables (SQLite)
This project includes multiple helper scripts that create/verify tables in `school.db`:
- `create_students_table.py`
- `create_teachers_table.py`
- `create_fees_table.py`
- `update_attendance_table.py`

Run them in this order:
```bash
python create_students_table.py
python create_teachers_table.py
python create_fees_table.py
python update_attendance_table.py
```

### 3) (If needed) Create/seed the admin user
The `create_db.py` script is for **PostgreSQL** (it uses `DATABASE_URL` and `psycopg2`).

For SQLite, ensure you have a `users` table and an admin account. If you already have `school.db` with users seeded, you can skip this.

---

## Run the Application

### Development
```bash
python app.py
```

### Production
A `Procfile` is included for Gunicorn:
- `web: gunicorn app:app`

---

## Default Routes
- `GET/POST /` : Login
- `GET /logout` : Logout

Role-based pages:
- Admin: `/admin/dashboard`, `/admin/students`, `/admin/teachers`, `/admin/notices`, `/admin/attendance`, `/admin/fees`
- Teacher: `/teacher/dashboard`, `/teacher/attendance`
- Student: `/student/dashboard`

---

## Project Structure
- `app.py` – Flask routes and session/role-based authorization
- `templates/` – Jinja2 HTML templates
- `static/` – CSS/JS/images
- `create_*.py` – Database table creation helpers

---

## Security Notes (Important)
- Password handling in this project is simplistic (plain-text in DB scripts and query).
- For any real deployment, replace with proper password hashing and secure credential storage.

---

## Troubleshooting
- **Tables missing / SQL errors:** re-run the SQLite helper scripts listed in *Setup (Local)*.
- **Admin login fails:** verify the `users` table exists and the admin credentials/roles are correct.

---

