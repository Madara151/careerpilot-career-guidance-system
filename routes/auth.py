from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from config.db import db


@app.route("/")
def home():
    return render_template("public/index.html")


@app.route("/about")
def about():
    return render_template("public/about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not full_name or not email or not message:
            flash("Name, email, and message are required.", "danger")
            return redirect(url_for("contact"))

        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO contact_messages
            (full_name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        """,
        (
            full_name,
            email,
            subject or None,
            message
        ))

        db.commit()

        flash("Thanks for reaching out! We'll get back to you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("public/contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")

        confirm_password = request.form.get("confirm_password")
        university = request.form.get("university")
        degree = request.form.get("degree")
        year_of_study = request.form.get("year_of_study")

        cursor = db.cursor(dictionary=True)

        # Check duplicate email
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user
        sql = """
        INSERT INTO users
        (full_name, email, password, role)
        VALUES (%s, %s, %s, %s)
        """

        values = (
            full_name,
            email,
            hashed_password,
            "student"
        )

        cursor.execute(sql, values)

        db.commit()

        user_id = cursor.lastrowid

        years_of_study = 0

        if year_of_study == "Year 1":
            years_of_study = 1
        elif year_of_study == "Year 2":
            years_of_study = 2
        elif year_of_study == "Year 3":
            years_of_study = 3
        elif year_of_study == "Year 4":
            years_of_study = 4

        profile_sql = """
            INSERT INTO student_profiles
            (
            user_id,
            university,
            degree,
            years_of_study
            )
            VALUES
            (
            %s,
            %s,
            %s,
            %s
            )
            """

        profile_values = (
            user_id,
            university,
            degree,
            years_of_study
        )

        cursor.execute(
            profile_sql,
            profile_values
        )

        db.commit()

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("public/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        # Email not found
        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        # Check password
        if not check_password_hash(
            user["password"],
            password
        ):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        # Create session
        session["user_id"] = user["user_id"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("student_dashboard"))

    return render_template("public/login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))