"""
Student Management System
A beginner-friendly Flask app that stores student records in SQLite.
"""

import os
import re
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

# The app object is the heart of Flask. Every route is attached to it.
app = Flask(__name__)

# Flask needs a secret key to show flash messages (success/error banners).
# This is fine for local learning. Do not use this value in a real public app.
app.secret_key = "student-management-local-secret"

# Store the database file next to this Python file.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "students.db")

# Allowed years of study. Using a list makes validation easier.
YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

# A simple pattern to check email format.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db_connection():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE)
    # This makes each row act like a dictionary: row["full_name"]
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the students table if it does not already exist."""
    connection = get_db_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            roll_number TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            course TEXT NOT NULL,
            year_of_study TEXT NOT NULL
        )
        """
    )
    connection.commit()
    connection.close()


def get_form_data():
    """Read student fields from the submitted form and trim extra spaces."""
    return {
        "full_name": request.form.get("full_name", "").strip(),
        "roll_number": request.form.get("roll_number", "").strip(),
        "email": request.form.get("email", "").strip(),
        "course": request.form.get("course", "").strip(),
        "year_of_study": request.form.get("year_of_study", "").strip(),
    }


def validate_student(data, student_id=None):
    """
    Check that all fields are valid.
    Returns a list of error messages. An empty list means the form is valid.
    """
    errors = []

    if not data["full_name"]:
        errors.append("Full name is required.")
    elif len(data["full_name"]) < 2:
        errors.append("Full name must be at least 2 characters.")
    elif len(data["full_name"]) > 80:
        errors.append("Full name must be 80 characters or less.")

    if not data["roll_number"]:
        errors.append("Roll number is required.")
    elif len(data["roll_number"]) > 20:
        errors.append("Roll number must be 20 characters or less.")

    if not data["email"]:
        errors.append("Email address is required.")
    elif not EMAIL_PATTERN.match(data["email"]):
        errors.append("Please enter a valid email address.")

    if not data["course"]:
        errors.append("Course is required.")
    elif len(data["course"]) > 60:
        errors.append("Course must be 60 characters or less.")

    if data["year_of_study"] not in YEARS:
        errors.append("Please select a valid year of study.")

    # Check for duplicate roll numbers, but allow a student to keep their own roll number.
    connection = get_db_connection()
    if student_id is None:
        existing = connection.execute(
            "SELECT id FROM students WHERE roll_number = ?",
            (data["roll_number"],),
        ).fetchone()
    else:
        existing = connection.execute(
            "SELECT id FROM students WHERE roll_number = ? AND id != ?",
            (data["roll_number"], student_id),
        ).fetchone()
    connection.close()

    if existing:
        errors.append("This roll number is already registered.")

    return errors


@app.route("/")
def index():
    """Home page: dashboard count, search bar, and student list."""
    search = request.args.get("q", "").strip()
    connection = get_db_connection()

    total_students = connection.execute(
        "SELECT COUNT(*) AS total FROM students"
    ).fetchone()["total"]

    if search:
        # LIKE with %search% finds matching names or roll numbers.
        like_term = f"%{search}%"
        students = connection.execute(
            """
            SELECT * FROM students
            WHERE full_name LIKE ? OR roll_number LIKE ?
            ORDER BY full_name COLLATE NOCASE
            """,
            (like_term, like_term),
        ).fetchall()
    else:
        students = connection.execute(
            "SELECT * FROM students ORDER BY full_name COLLATE NOCASE"
        ).fetchall()

    connection.close()
    return render_template(
        "index.html",
        students=students,
        total_students=total_students,
        search=search,
    )


@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    """Show the add form, or save a new student when the form is submitted."""
    if request.method == "POST":
        data = get_form_data()
        errors = validate_student(data)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "student_form.html",
                mode="add",
                student=data,
                years=YEARS,
            )

        connection = get_db_connection()
        connection.execute(
            """
            INSERT INTO students (full_name, roll_number, email, course, year_of_study)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["full_name"],
                data["roll_number"],
                data["email"],
                data["course"],
                data["year_of_study"],
            ),
        )
        connection.commit()
        connection.close()
        flash("Student added successfully.", "success")
        return redirect(url_for("index"))

    empty_student = {
        "full_name": "",
        "roll_number": "",
        "email": "",
        "course": "",
        "year_of_study": "",
    }
    return render_template(
        "student_form.html",
        mode="add",
        student=empty_student,
        years=YEARS,
    )


@app.route("/students/<int:student_id>")
def view_student(student_id):
    """Show one student's details in read-only mode."""
    connection = get_db_connection()
    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,),
    ).fetchone()
    connection.close()

    if student is None:
        flash("Student not found.", "error")
        return redirect(url_for("index"))

    return render_template(
        "student_form.html",
        mode="view",
        student=student,
        years=YEARS,
    )


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    """Show the edit form, or update an existing student."""
    connection = get_db_connection()
    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,),
    ).fetchone()

    if student is None:
        connection.close()
        flash("Student not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        data = get_form_data()
        errors = validate_student(data, student_id=student_id)

        if errors:
            connection.close()
            for error in errors:
                flash(error, "error")
            return render_template(
                "student_form.html",
                mode="edit",
                student=data,
                student_id=student_id,
                years=YEARS,
            )

        connection.execute(
            """
            UPDATE students
            SET full_name = ?, roll_number = ?, email = ?, course = ?, year_of_study = ?
            WHERE id = ?
            """,
            (
                data["full_name"],
                data["roll_number"],
                data["email"],
                data["course"],
                data["year_of_study"],
                student_id,
            ),
        )
        connection.commit()
        connection.close()
        flash("Student updated successfully.", "success")
        return redirect(url_for("index"))

    connection.close()
    return render_template(
        "student_form.html",
        mode="edit",
        student=student,
        student_id=student_id,
        years=YEARS,
    )


@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    """Delete a student after the user confirms in the browser."""
    connection = get_db_connection()
    student = connection.execute(
        "SELECT id FROM students WHERE id = ?",
        (student_id,),
    ).fetchone()

    if student is None:
        connection.close()
        flash("Student not found.", "error")
        return redirect(url_for("index"))

    connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
    connection.commit()
    connection.close()
    flash("Student deleted successfully.", "success")
    return redirect(url_for("index"))


# Create the table as soon as the app starts.
with app.app_context():
    init_db()


if __name__ == "__main__":
    # debug=True reloads the app when you save files. Use this only while learning.
    app.run(debug=True)
