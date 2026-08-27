import os
from datetime import datetime

import pdfplumber
from flask import render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from config.db import db
from services.roadmap_generator import generate_learning_roadmap
from services.career_recommender import get_career_recommendations


@app.route("/student/dashboard")
def student_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    # Get profile
    cursor.execute("""
    SELECT
    sp.*,
    c.career_name
    FROM student_profiles sp

    LEFT JOIN careers c
    ON sp.target_career_id = c.career_id

    WHERE sp.user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    # =========================
    # PROFILE COMPLETION
    # =========================
    # Checks 8 concrete fields so the percentage is real and moves
    # as the student actually fills things in, rather than a fixed
    # placeholder number.

    profile_completion = 0

    if profile:

        profile_id = profile["profile_id"]

        completion_checks = [
            bool(profile["university"]),
            bool(profile["degree"]),
            bool(profile["years_of_study"]),
            bool(profile["bio"]),
            bool(profile["profile_picture"]),
            bool(profile["target_career_id"]),
        ]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM student_skills
            WHERE profile_id=%s
        """, (profile_id,))

        completion_checks.append(cursor.fetchone()["total"] > 0)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM resumes
            WHERE profile_id=%s
        """, (profile_id,))

        completion_checks.append(cursor.fetchone()["total"] > 0)

        profile_completion = round(
            (sum(completion_checks) / len(completion_checks)) * 100
        )

    # Default values
    match_percentage = 0
    skills_owned = 0
    skills_missing = 0
    roadmap_progress = 0
    missing_skills = []
    recommendation = None

    # Only calculate if a target career exists
    if profile and profile["target_career_id"]:

        career_id = profile["target_career_id"]
        profile_id = profile["profile_id"]

        # =========================
        # GET CAREER SKILLS
        # =========================

        cursor.execute("""
            SELECT skill_id
            FROM career_skills
            WHERE career_id=%s
        """, (career_id,))

        required_skills = cursor.fetchall()

        required_ids = {
            row["skill_id"]
            for row in required_skills
        }

        # =========================
        # GET STUDENT SKILLS
        # =========================

        cursor.execute("""
            SELECT skill_id
            FROM student_skills
            WHERE profile_id=%s
        """, (profile_id,))

        student_skills = cursor.fetchall()

        student_ids = {
            row["skill_id"]
            for row in student_skills
        }

        # =========================
        # CALCULATE PERCENTAGE
        # =========================

        matched_ids = required_ids.intersection(
            student_ids
        )

        # Get missing skills with names
        cursor.execute("""
        SELECT
            s.skill_name
        FROM career_skills cs
        JOIN skills s
        ON cs.skill_id = s.skill_id
        WHERE cs.career_id=%s
        AND cs.skill_id NOT IN (
            SELECT skill_id
            FROM student_skills
            WHERE profile_id=%s
        )
        ORDER BY s.skill_name
        """, (career_id, profile_id))

        missing_skills = cursor.fetchall()

        if len(missing_skills) > 0:
            recommendation = (
                "Start learning " +
                missing_skills[0]["skill_name"] +
                " first."
            )

        if len(required_ids) > 0:

            match_percentage = round(
                (
                    len(matched_ids)
                    /
                    len(required_ids)
                ) * 100
            )

        skills_owned = len(student_ids)

        skills_missing = len(
            required_ids - student_ids
        )

        # =========================
        # ROADMAP PROGRESS
        # =========================

        cursor.execute("""
        SELECT COUNT(*) AS total_steps
        FROM learning_roadmaps
        WHERE profile_id=%s
        """, (profile_id,))

        total_steps = cursor.fetchone()["total_steps"]

        cursor.execute("""
        SELECT COUNT(*) AS completed_steps
        FROM learning_roadmaps
        WHERE profile_id=%s
        AND status='Completed'
        """, (profile_id,))

        completed_steps = cursor.fetchone()["completed_steps"]

        roadmap_progress = 0

        if total_steps > 0:
            roadmap_progress = round(
                (completed_steps / total_steps) * 100
            )

    return render_template(
        "student/dashboard.html",
        profile=profile,
        profile_completion=profile_completion,
        match_percentage=match_percentage,
        skills_owned=skills_owned,
        skills_missing=skills_missing,
        missing_skills=missing_skills,
        recommendation=recommendation,
        roadmap_progress=roadmap_progress
    )


@app.route("/student/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            u.full_name,
            u.email,
            u.created_at,
            sp.*,
            c.career_name
        FROM student_profiles sp

        JOIN users u
        ON sp.user_id = u.user_id

        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id

        WHERE sp.user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("student_dashboard"))

    profile_id = profile["profile_id"]

    cursor.execute("""
        SELECT COUNT(*) AS skill_count
        FROM student_skills
        WHERE profile_id=%s
    """, (profile_id,))

    skill_count = cursor.fetchone()["skill_count"]

    cursor.execute("""
        SELECT COUNT(*) AS completed_steps
        FROM learning_roadmaps
        WHERE profile_id=%s
        AND status='Completed'
    """, (profile_id,))

    completed_steps = cursor.fetchone()["completed_steps"]

    return render_template(
        "student/profile.html",
        profile=profile,
        skill_count=skill_count,
        completed_steps=completed_steps
    )


@app.route("/student/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            u.full_name,
            u.email,
            sp.*
        FROM student_profiles sp

        JOIN users u
        ON sp.user_id = u.user_id

        WHERE sp.user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("student_dashboard"))

    profile_id = profile["profile_id"]

    if request.method == "POST":

        full_name = request.form.get("full_name")
        university = request.form.get("university")
        degree = request.form.get("degree")
        year_of_study = request.form.get("years_of_study")
        bio = request.form.get("bio")

        years_of_study = None

        if year_of_study and year_of_study.isdigit():
            years_of_study = int(year_of_study)

        # =========================
        # Profile picture upload
        # =========================

        picture_file = request.files.get("profile_picture")

        allowed_extensions = (".jpg", ".jpeg", ".png", ".webp")

        if picture_file and picture_file.filename != "":

            ext = os.path.splitext(picture_file.filename)[1].lower()

            if ext not in allowed_extensions:

                flash(
                    "Profile picture must be a JPG, PNG, or WEBP image.",
                    "danger"
                )
                return redirect(url_for("edit_profile"))

            new_filename = (
                "profile_"
                + str(profile_id)
                + "_"
                + datetime.now().strftime("%Y%m%d%H%M%S")
                + ext
            )

            new_filepath = os.path.join(
                app.config["PROFILE_UPLOAD_FOLDER"],
                new_filename
            )

            picture_file.save(new_filepath)

            # Delete old picture if one exists
            if profile["profile_picture"]:

                old_path = os.path.join(
                    app.config["PROFILE_UPLOAD_FOLDER"],
                    profile["profile_picture"]
                )

                if os.path.exists(old_path):
                    os.remove(old_path)

            cursor.execute("""
                UPDATE student_profiles
                SET profile_picture=%s
                WHERE profile_id=%s
            """,
            (
                new_filename,
                profile_id
            ))

        # =========================
        # Update text fields
        # =========================

        cursor.execute("""
            UPDATE users
            SET full_name=%s
            WHERE user_id=%s
        """,
        (
            full_name,
            user_id
        ))

        cursor.execute("""
            UPDATE student_profiles
            SET
                university=%s,
                degree=%s,
                years_of_study=%s,
                bio=%s
            WHERE profile_id=%s
        """,
        (
            university,
            degree,
            years_of_study,
            bio,
            profile_id
        ))

        db.commit()

        # Keep the sidebar/header name in sync with the new name
        session["full_name"] = full_name

        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template(
        "student/edit_profile.html",
        profile=profile
    )


@app.route(
    "/student/career-selection",
    methods=["GET", "POST"]
)
def career_selection():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    user_id = session["user_id"]

    if request.method == "POST":

        career_id = request.form.get("career_id")

        cursor.execute("""
            UPDATE student_profiles
            SET target_career_id=%s
            WHERE user_id=%s
        """,
        (
            career_id,
            user_id
        ))

        db.commit()

        cursor.execute("""
        SELECT profile_id
        FROM student_profiles
        WHERE user_id=%s
        """, (user_id,))

        profile = cursor.fetchone()

        generate_learning_roadmap(
            profile["profile_id"],
            int(career_id)
        )

        flash("Target career updated.", "success")

        return redirect(
            url_for("student_dashboard")
        )

    cursor.execute("""
        SELECT *
        FROM careers
    """)

    careers = cursor.fetchall()

    return render_template(
        "student/career_selection.html",
        careers=careers
    )


@app.route("/student/roadmap")
def roadmap():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sp.*,
            c.career_name
        FROM student_profiles sp
        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id
        WHERE sp.user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("student_dashboard"))

    profile_id = profile["profile_id"]

    cursor.execute("""
        SELECT *
        FROM learning_roadmaps
        WHERE profile_id=%s
        ORDER BY step_no
    """, (profile_id,))

    roadmap = cursor.fetchall()

    return render_template(
        "student/roadmap.html",
        profile=profile,
        roadmap=roadmap
    )


@app.route("/student/start-roadmap/<int:roadmap_id>")
def start_roadmap(roadmap_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute("""
        UPDATE learning_roadmaps
        SET status='In Progress'
        WHERE roadmap_id=%s
    """, (roadmap_id,))

    db.commit()

    return redirect(url_for("roadmap"))


@app.route("/student/complete-roadmap/<int:roadmap_id>")
def complete_roadmap(roadmap_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute("""
        UPDATE learning_roadmaps
        SET status='Completed'
        WHERE roadmap_id=%s
    """, (roadmap_id,))

    db.commit()

    return redirect(url_for("roadmap"))


@app.route("/student/skills", methods=["GET", "POST"])
def student_skills():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    user_id = session["user_id"]

    # Get profile
    cursor.execute("""
        SELECT profile_id
        FROM student_profiles
        WHERE user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    profile_id = profile["profile_id"]

    # Add skill
    if request.method == "POST":

        skill_id = request.form.get("skill_id")

        cursor.execute("""
            SELECT *
            FROM student_skills
            WHERE profile_id=%s
            AND skill_id=%s
        """, (profile_id, skill_id))

        existing = cursor.fetchone()

        if not existing:

            cursor.execute("""
                INSERT INTO student_skills
                (
                    profile_id,
                    skill_id,
                    proficiency_level
                )
                VALUES
                (
                    %s,
                    %s,
                    NULL
                )
            """,
            (
                profile_id,
                skill_id
            ))

            db.commit()

            # Get student's target career
            cursor.execute("""
                SELECT target_career_id
                FROM student_profiles
                WHERE profile_id=%s
            """, (profile_id,))

            career = cursor.fetchone()

            # Regenerate roadmap
            if career and career["target_career_id"]:

                generate_learning_roadmap(
                    profile_id,
                    career["target_career_id"]
                )

        return redirect(url_for("student_skills"))

    # Get all available skills
    cursor.execute("""
        SELECT *
        FROM skills
        ORDER BY skill_name
    """)

    skills = cursor.fetchall()

    # Get student's skills
    cursor.execute("""
        SELECT
            ss.student_skill_id,
            s.skill_name,
            ss.proficiency_level

        FROM student_skills ss

        JOIN skills s
        ON ss.skill_id = s.skill_id

        WHERE ss.profile_id=%s

        ORDER BY s.skill_name
    """, (profile_id,))

    my_skills = cursor.fetchall()

    return render_template(
        "student/skills.html",
        skills=skills,
        my_skills=my_skills
    )


@app.route("/student/delete-skill/<int:id>")
def delete_skill(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        DELETE
        FROM student_skills
        WHERE student_skill_id=%s
    """, (id,))

    db.commit()

    cursor.execute("""
        SELECT
            profile_id,
            target_career_id
        FROM student_profiles
        WHERE user_id=%s
    """, (session["user_id"],))

    profile = cursor.fetchone()

    if profile and profile["target_career_id"]:

        generate_learning_roadmap(
            profile["profile_id"],
            profile["target_career_id"]
        )

    return redirect(url_for("student_skills"))


@app.route("/student/career-match")
def career_match():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sp.*,
            c.career_name
        FROM student_profiles sp

        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id

        WHERE sp.user_id=%s
    """, (user_id,))
    profile = cursor.fetchone()

    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("student_dashboard"))

    profile_id = profile["profile_id"]

    if not profile["target_career_id"]:
        return render_template(
            "student/career_match.html",
            profile=profile,
            match_percentage=0,
            required_skills=[],
            missing_skills=[],
            matched_count=0,
            missing_count=0
        )

    career_id = profile["target_career_id"]

    # Student skills
    cursor.execute("""
        SELECT skill_id
        FROM student_skills
        WHERE profile_id = %s
    """, (profile_id,))
    student_skill_rows = cursor.fetchall()
    student_skill_ids = {row["skill_id"] for row in student_skill_rows}

    # Career required skills
    cursor.execute("""
        SELECT s.skill_id, s.skill_name
        FROM career_skills cs
        JOIN skills s ON cs.skill_id = s.skill_id
        WHERE cs.career_id = %s
    """, (career_id,))
    career_skills = cursor.fetchall()

    required_ids = {row["skill_id"] for row in career_skills}

    # Matching logic
    matched_ids = student_skill_ids.intersection(required_ids)
    missing_ids = required_ids - student_skill_ids

    required_skills = [row["skill_name"] for row in career_skills]
    missing_skills = [
        row["skill_name"] for row in career_skills
        if row["skill_id"] in missing_ids
    ]

    match_percentage = 0
    if required_ids:
        match_percentage = int((len(matched_ids) / len(required_ids)) * 100)

    return render_template(
        "student/career_match.html",
        profile=profile,
        match_percentage=match_percentage,
        required_skills=required_skills,
        missing_skills=missing_skills,
        matched_count=len(matched_ids),
        missing_count=len(missing_ids)
    )


@app.route("/student/career-recommendations")
def career_recommendations():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sp.profile_id,
            sp.target_career_id,
            c.career_name AS target_career_name
        FROM student_profiles sp

        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id

        WHERE sp.user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("student_dashboard"))

    profile_id = profile["profile_id"]

    # Student's current skills
    cursor.execute("""
        SELECT s.skill_name
        FROM student_skills ss
        JOIN skills s ON s.skill_id = ss.skill_id
        WHERE ss.profile_id=%s
    """, (profile_id,))

    student_skill_names = [row["skill_name"] for row in cursor.fetchall()]

    # Every career, with its required skills grouped in
    cursor.execute("""
        SELECT
            c.career_id,
            c.career_name,
            c.description,
            s.skill_name
        FROM careers c

        LEFT JOIN career_skills cs
        ON cs.career_id = c.career_id

        LEFT JOIN skills s
        ON s.skill_id = cs.skill_id

        ORDER BY c.career_name
    """)

    careers_map = {}

    for row in cursor.fetchall():

        career_id = row["career_id"]

        if career_id not in careers_map:

            careers_map[career_id] = {
                "career_id": career_id,
                "career_name": row["career_name"],
                "description": row["description"],
                "skills": []
            }

        if row["skill_name"]:
            careers_map[career_id]["skills"].append(row["skill_name"])

    careers_with_skills = list(careers_map.values())

    recommendations = get_career_recommendations(
        student_skill_names,
        careers_with_skills
    )

    return render_template(
        "student/career_recommendations.html",
        profile=profile,
        recommendations=recommendations,
        skills_owned_count=len(student_skill_names)
    )


@app.route("/student/resume", methods=["GET", "POST"])
def resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    # Get student profile
    cursor.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    profile_id = profile["profile_id"]

    # ==========================
    # Upload Resume
    # ==========================

    if request.method == "POST":

        file = request.files.get("resume")

        if not file or file.filename == "":
            flash("Please select a PDF file.", "danger")
            return redirect(url_for("resume"))

        if not file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are allowed.", "danger")
            return redirect(url_for("resume"))

        # Create unique filename
        filename = (
            str(profile_id)
            + "_"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + ".pdf"
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)

        # Check if resume already exists
        cursor.execute("""
            SELECT *
            FROM resumes
            WHERE profile_id=%s
        """, (profile_id,))

        existing_resume = cursor.fetchone()

        if existing_resume:

            # Delete old PDF from folder
            old_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                existing_resume["file_name"]
            )

            if os.path.exists(old_path):
                os.remove(old_path)

            # Update database
            cursor.execute("""
                UPDATE resumes

                SET
                    file_name=%s,
                    update_date=NOW()

                WHERE profile_id=%s
            """,
            (
                filename,
                profile_id
            ))

        else:

            # Insert new record
            cursor.execute("""
                INSERT INTO resumes
                (
                    profile_id,
                    file_name,
                    update_date
                )

                VALUES
                (
                    %s,
                    %s,
                    NOW()
                )
            """,
            (
                profile_id,
                filename
            ))

        db.commit()

        flash("Resume uploaded successfully!", "success")
        return redirect(url_for("resume"))

    # ==========================
    # Load Resume
    # ==========================

    cursor.execute("""
        SELECT *
        FROM resumes
        WHERE profile_id=%s
    """, (profile_id,))

    resume = cursor.fetchone()

    # ==========================
    # Default values
    # ==========================

    extracted_text = ""

    detected_skills = []
    required_skills = []
    missing_skills = []
    recommendations = []

    match_percentage = 0

    # ==========================
    # Only analyze if resume exists
    # ==========================

    if resume:

        pdf_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            resume["file_name"]
        )

        if os.path.exists(pdf_path):

            with pdfplumber.open(pdf_path) as pdf:

                for page in pdf.pages:

                    extracted_text += page.extract_text() or ""

        # Load all skills
        cursor.execute("""
            SELECT DISTINCT skill_name
            FROM skills
            ORDER BY skill_name
        """)

        all_skills = cursor.fetchall()

        resume_text = extracted_text.lower()

        # Detect skills
        for row in all_skills:

            skill = row["skill_name"]

            if skill.lower() in resume_text:

                detected_skills.append(skill)

        # Compare with career only if target career exists
        if profile["target_career_id"]:

            cursor.execute("""
                SELECT
                    s.skill_name

                FROM career_skills cs

                JOIN skills s
                ON cs.skill_id = s.skill_id

                WHERE cs.career_id=%s
            """, (profile["target_career_id"],))

            career_skills = cursor.fetchall()

            for row in career_skills:

                required_skills.append(
                    row["skill_name"]
                )

            for skill in required_skills:

                if skill not in detected_skills:

                    missing_skills.append(skill)

            matched = len(required_skills) - len(missing_skills)

            if required_skills:

                match_percentage = round(
                    (matched / len(required_skills)) * 100
                )

            for skill in missing_skills:

                recommendations.append(
                    "Improve your knowledge in " + skill
                )

    return render_template(

        "student/resume.html",

        profile=profile,

        resume=resume,

        detected_skills=detected_skills,

        required_skills=required_skills,

        missing_skills=missing_skills,

        recommendations=recommendations,

        match_percentage=match_percentage

    )


@app.route("/uploads/resumes/<filename>")
def uploaded_resume(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


@app.route("/student/delete-resume")
def delete_resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT profile_id
        FROM student_profiles
        WHERE user_id=%s
    """, (session["user_id"],))

    profile = cursor.fetchone()

    profile_id = profile["profile_id"]

    cursor.execute("""
        SELECT *
        FROM resumes
        WHERE profile_id=%s
    """, (profile_id,))

    resume = cursor.fetchone()

    if resume:

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            resume["file_name"]
        )

        if os.path.exists(filepath):
            os.remove(filepath)

        cursor.execute("""
            DELETE FROM resumes
            WHERE profile_id=%s
        """, (profile_id,))

        db.commit()

    flash("Resume deleted.", "success")
    return redirect(url_for("resume"))


@app.route("/student/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sp.*,
            c.career_name
        FROM student_profiles sp

        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id

        WHERE sp.user_id=%s
    """, (user_id,))

    profile = cursor.fetchone()

    if not profile:
        flash("Profile not found.", "danger")
        return redirect(url_for("student_dashboard"))

    profile_id = profile["profile_id"]

    recommended_courses = []
    other_courses = []

    if profile["target_career_id"]:

        career_id = profile["target_career_id"]

        # Courses tied to the skills the student is still missing
        # for their target career.
        cursor.execute("""
            SELECT DISTINCT
                co.course_id,
                co.course_name,
                co.provider,
                co.course_link,
                co.description,
                s.skill_name

            FROM career_skills cs

            JOIN skill_courses sc
            ON sc.skill_id = cs.skill_id

            JOIN courses co
            ON co.course_id = sc.course_id

            JOIN skills s
            ON s.skill_id = cs.skill_id

            WHERE cs.career_id=%s

            AND cs.skill_id NOT IN (
                SELECT skill_id
                FROM student_skills
                WHERE profile_id=%s
            )

            ORDER BY s.skill_name
        """, (career_id, profile_id))

        recommended_courses = cursor.fetchall()

    recommended_ids = {c["course_id"] for c in recommended_courses}

    # Everything else, so the page still has content for skills
    # outside the student's target career, or if they have no
    # target career selected yet.
    cursor.execute("""
        SELECT
            course_id,
            course_name,
            provider,
            course_link,
            description
        FROM courses
        ORDER BY course_name
    """)

    for row in cursor.fetchall():
        if row["course_id"] not in recommended_ids:
            other_courses.append(row)

    return render_template(
        "student/courses.html",
        profile=profile,
        recommended_courses=recommended_courses,
        other_courses=other_courses
    )


@app.route(
    "/student/import-selected-skills",
    methods=["POST"]
)
def import_selected_skills():

    if "user_id" not in session:
        return redirect(url_for("login"))

    selected_skills = request.form.getlist("skills")

    cursor = db.cursor(dictionary=True)

    # Get Student Profile
    cursor.execute("""
        SELECT *
        FROM student_profiles
        WHERE user_id=%s
    """, (session["user_id"],))

    profile = cursor.fetchone()

    profile_id = profile["profile_id"]

    # Insert Selected Skills
    for skill_name in selected_skills:

        cursor.execute("""
            SELECT skill_id
            FROM skills
            WHERE skill_name=%s
        """, (skill_name,))

        skill = cursor.fetchone()

        if not skill:
            continue

        skill_id = skill["skill_id"]

        # Avoid duplicates
        cursor.execute("""
            SELECT *
            FROM student_skills
            WHERE profile_id=%s
            AND skill_id=%s
        """,
        (
            profile_id,
            skill_id
        ))

        existing = cursor.fetchone()

        if not existing:

            cursor.execute("""
                INSERT INTO student_skills
                (
                    profile_id,
                    skill_id,
                    proficiency_level
                )

                VALUES
                (
                    %s,
                    %s,
                    NULL
                )
            """,
            (
                profile_id,
                skill_id
            ))

    db.commit()

    # Update Learning Roadmap
    if profile["target_career_id"]:

        generate_learning_roadmap(
            profile_id,
            profile["target_career_id"]
        )

    flash("Skills imported successfully.", "success")
    return redirect(url_for("student_skills"))


@app.route("/student/settings", methods=["GET", "POST"])
def student_settings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        action = request.form.get("action")

        # =========================
        # CHANGE PASSWORD
        # =========================

        if action == "password":

            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            cursor.execute("""
                SELECT password
                FROM users
                WHERE user_id=%s
            """, (user_id,))

            user = cursor.fetchone()

            if not check_password_hash(user["password"], current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("student_settings"))

            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for("student_settings"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("student_settings"))

            cursor.execute("""
                UPDATE users
                SET password=%s
                WHERE user_id=%s
            """,
            (
                generate_password_hash(new_password),
                user_id
            ))

            db.commit()

            flash("Password changed successfully.", "success")
            return redirect(url_for("student_settings"))

        # =========================
        # DELETE ACCOUNT
        # =========================

        if action == "delete_account":

            confirm_password = request.form.get("confirm_password", "")

            cursor.execute("""
                SELECT password
                FROM users
                WHERE user_id=%s
            """, (user_id,))

            user = cursor.fetchone()

            if not check_password_hash(user["password"], confirm_password):
                flash("Password incorrect. Account was not deleted.", "danger")
                return redirect(url_for("student_settings"))

            cursor.execute("""
                SELECT profile_id, profile_picture
                FROM student_profiles
                WHERE user_id=%s
            """, (user_id,))

            profile = cursor.fetchone()

            if profile:

                # Remove the resume file from disk, if one exists.
                cursor.execute("""
                    SELECT file_name
                    FROM resumes
                    WHERE profile_id=%s
                """, (profile["profile_id"],))

                resume = cursor.fetchone()

                if resume:

                    resume_path = os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        resume["file_name"]
                    )

                    if os.path.exists(resume_path):
                        os.remove(resume_path)

                # Remove the profile picture from disk, if one exists.
                if profile["profile_picture"]:

                    picture_path = os.path.join(
                        app.config["PROFILE_UPLOAD_FOLDER"],
                        profile["profile_picture"]
                    )

                    if os.path.exists(picture_path):
                        os.remove(picture_path)

            # student_profiles, student_skills, learning_roadmaps,
            # progress_tracking, and resumes all cascade-delete via
            # ON DELETE CASCADE once the users row is gone.
            cursor.execute("""
                DELETE FROM users
                WHERE user_id=%s
            """, (user_id,))

            db.commit()

            session.clear()

            flash("Your account has been permanently deleted.", "success")
            return redirect(url_for("login"))

    cursor.execute("""
        SELECT full_name, email, created_at
        FROM users
        WHERE user_id=%s
    """, (user_id,))

    student_user = cursor.fetchone()

    return render_template(
        "student/settings.html",
        student_user=student_user
    )