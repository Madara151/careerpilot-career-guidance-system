import os
from functools import wraps

from flask import render_template, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from config.db import db
from services.roadmap_generator import generate_learning_roadmap


def admin_required(view_func):
    """
    Guards admin-only routes. Redirects non-logged-in users to login,
    and logged-in students to their own dashboard instead of exposing
    a 403 — keeps behavior consistent with the rest of the app, which
    always redirects rather than erroring.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("student_dashboard"))

        return view_func(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_sidebar_unread_count():
    """
    Makes the unread contact-message count available to every template
    (used by admin/_sidebar.html) without having to pass it explicitly
    from every single admin route.
    """

    if session.get("role") != "admin":
        return dict(sidebar_unread_count=0)

    # Wrapped in try/except so the admin panel doesn't break entirely
    # if contact_messages hasn't been created yet (see
    # migration_add_contact_messages.sql).
    try:

        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM contact_messages
            WHERE is_read = 0
        """)

        return dict(sidebar_unread_count=cursor.fetchone()["total"])

    except Exception:
        return dict(sidebar_unread_count=0)


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    cursor = db.cursor(dictionary=True)

    # =========================
    # TOP-LEVEL COUNTS
    # =========================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role='student'
    """)
    total_students = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM careers")
    total_careers = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM skills")
    total_skills = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM courses")
    total_courses = cursor.fetchone()["total"]

    # =========================
    # RECENT STUDENTS
    # =========================

    cursor.execute("""
        SELECT
            u.full_name,
            u.email,
            u.created_at,
            sp.university,
            c.career_name
        FROM users u

        JOIN student_profiles sp
        ON sp.user_id = u.user_id

        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id

        WHERE u.role='student'

        ORDER BY u.created_at DESC

        LIMIT 5
    """)

    recent_students = cursor.fetchall()

    # =========================
    # MOST TARGETED CAREERS
    # =========================

    cursor.execute("""
        SELECT
            c.career_name,
            COUNT(sp.profile_id) AS student_count

        FROM careers c

        LEFT JOIN student_profiles sp
        ON sp.target_career_id = c.career_id

        GROUP BY c.career_id, c.career_name

        ORDER BY student_count DESC, c.career_name ASC

        LIMIT 5
    """)

    popular_careers = cursor.fetchall()

    max_popular_count = 0

    if popular_careers:
        max_popular_count = max(
            row["student_count"] for row in popular_careers
        )

    # =========================
    # ROADMAP PROGRESS SNAPSHOT
    # =========================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM learning_roadmaps
    """)
    total_roadmap_steps = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM learning_roadmaps
        WHERE status='Completed'
    """)
    completed_roadmap_steps = cursor.fetchone()["total"]

    overall_completion = 0

    if total_roadmap_steps > 0:
        overall_completion = round(
            (completed_roadmap_steps / total_roadmap_steps) * 100
        )

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_careers=total_careers,
        total_skills=total_skills,
        total_courses=total_courses,
        recent_students=recent_students,
        popular_careers=popular_careers,
        max_popular_count=max_popular_count,
        overall_completion=overall_completion
    )


@app.route("/admin/careers")
@admin_required
def admin_careers():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            c.career_id,
            c.career_name,
            c.description,

            (
                SELECT COUNT(*)
                FROM career_skills cs
                WHERE cs.career_id = c.career_id
            ) AS skill_count,

            (
                SELECT COUNT(*)
                FROM student_profiles sp
                WHERE sp.target_career_id = c.career_id
            ) AS student_count

        FROM careers c

        ORDER BY c.career_name
    """)

    careers = cursor.fetchall()

    return render_template(
        "admin/careers.html",
        careers=careers
    )


@app.route("/admin/add-career", methods=["GET", "POST"])
@admin_required
def add_career():

    if request.method == "POST":

        career_name = request.form.get("career_name", "").strip()
        description = request.form.get("description", "").strip()

        if not career_name:
            flash("Career name is required.", "danger")
            return redirect(url_for("add_career"))

        cursor = db.cursor(dictionary=True)

        # Prevent duplicate career names
        cursor.execute("""
            SELECT career_id
            FROM careers
            WHERE career_name=%s
        """, (career_name,))

        existing = cursor.fetchone()

        if existing:
            flash("A career with this name already exists.", "danger")
            return redirect(url_for("add_career"))

        cursor.execute("""
            INSERT INTO careers
            (career_name, description)
            VALUES (%s, %s)
        """,
        (
            career_name,
            description or None
        ))

        db.commit()

        flash("Career added successfully.", "success")
        return redirect(url_for("admin_careers"))

    return render_template("admin/add_career.html")


@app.route("/admin/edit-career/<int:career_id>", methods=["GET", "POST"])
@admin_required
def edit_career(career_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM careers
        WHERE career_id=%s
    """, (career_id,))

    career = cursor.fetchone()

    if not career:
        flash("Career not found.", "danger")
        return redirect(url_for("admin_careers"))

    if request.method == "POST":

        career_name = request.form.get("career_name", "").strip()
        description = request.form.get("description", "").strip()

        if not career_name:
            flash("Career name is required.", "danger")
            return redirect(url_for("edit_career", career_id=career_id))

        # Prevent renaming to a name already used by a different career
        cursor.execute("""
            SELECT career_id
            FROM careers
            WHERE career_name=%s
            AND career_id != %s
        """, (career_name, career_id))

        existing = cursor.fetchone()

        if existing:
            flash("Another career already uses this name.", "danger")
            return redirect(url_for("edit_career", career_id=career_id))

        cursor.execute("""
            UPDATE careers
            SET
                career_name=%s,
                description=%s
            WHERE career_id=%s
        """,
        (
            career_name,
            description or None,
            career_id
        ))

        db.commit()

        flash("Career updated successfully.", "success")
        return redirect(url_for("admin_careers"))

    return render_template(
        "admin/edit_career.html",
        career=career
    )


@app.route("/admin/delete-career/<int:career_id>")
@admin_required
def delete_career(career_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT career_name
        FROM careers
        WHERE career_id=%s
    """, (career_id,))

    career = cursor.fetchone()

    if not career:
        flash("Career not found.", "danger")
        return redirect(url_for("admin_careers"))

    # career_skills, learning_roadmaps rows cascade-delete via FK
    # ON DELETE CASCADE. student_profiles.target_career_id is set
    # to NULL via ON DELETE SET NULL, so students aren't deleted,
    # they just lose their target career.
    cursor.execute("""
        DELETE FROM careers
        WHERE career_id=%s
    """, (career_id,))

    db.commit()

    flash(
        "Career \"" + career["career_name"] + "\" deleted.",
        "success"
    )
    return redirect(url_for("admin_careers"))


@app.route("/admin/skills")
@admin_required
def admin_skills():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.skill_id,
            s.skill_name,
            s.category,

            (
                SELECT COUNT(*)
                FROM career_skills cs
                WHERE cs.skill_id = s.skill_id
            ) AS career_count,

            (
                SELECT COUNT(*)
                FROM student_skills ss
                WHERE ss.skill_id = s.skill_id
            ) AS student_count

        FROM skills s

        ORDER BY s.category, s.skill_name
    """)

    skills = cursor.fetchall()

    # Existing categories, used to populate a datalist on the add/edit
    # forms so admins reuse the same category names instead of creating
    # near-duplicates like "Cloud" vs "Cloud Computing".
    cursor.execute("""
        SELECT DISTINCT category
        FROM skills
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
    """)

    categories = [row["category"] for row in cursor.fetchall()]

    return render_template(
        "admin/skills.html",
        skills=skills,
        categories=categories
    )


@app.route("/admin/add-skill", methods=["GET", "POST"])
@admin_required
def add_skill():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT DISTINCT category
        FROM skills
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
    """)

    categories = [row["category"] for row in cursor.fetchall()]

    if request.method == "POST":

        skill_name = request.form.get("skill_name", "").strip()
        category = request.form.get("category", "").strip()

        if not skill_name:
            flash("Skill name is required.", "danger")
            return redirect(url_for("add_skill"))

        # Prevent duplicate skill names
        cursor.execute("""
            SELECT skill_id
            FROM skills
            WHERE skill_name=%s
        """, (skill_name,))

        existing = cursor.fetchone()

        if existing:
            flash("A skill with this name already exists.", "danger")
            return redirect(url_for("add_skill"))

        cursor.execute("""
            INSERT INTO skills
            (skill_name, category)
            VALUES (%s, %s)
        """,
        (
            skill_name,
            category or None
        ))

        db.commit()

        flash("Skill added successfully.", "success")
        return redirect(url_for("admin_skills"))

    return render_template(
        "admin/add_skill.html",
        categories=categories
    )


@app.route("/admin/edit-skill/<int:skill_id>", methods=["GET", "POST"])
@admin_required
def edit_skill(skill_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM skills
        WHERE skill_id=%s
    """, (skill_id,))

    skill = cursor.fetchone()

    if not skill:
        flash("Skill not found.", "danger")
        return redirect(url_for("admin_skills"))

    cursor.execute("""
        SELECT DISTINCT category
        FROM skills
        WHERE category IS NOT NULL
        AND category != ''
        ORDER BY category
    """)

    categories = [row["category"] for row in cursor.fetchall()]

    if request.method == "POST":

        skill_name = request.form.get("skill_name", "").strip()
        category = request.form.get("category", "").strip()

        if not skill_name:
            flash("Skill name is required.", "danger")
            return redirect(url_for("edit_skill", skill_id=skill_id))

        # Prevent renaming to a name already used by a different skill
        cursor.execute("""
            SELECT skill_id
            FROM skills
            WHERE skill_name=%s
            AND skill_id != %s
        """, (skill_name, skill_id))

        existing = cursor.fetchone()

        if existing:
            flash("Another skill already uses this name.", "danger")
            return redirect(url_for("edit_skill", skill_id=skill_id))

        cursor.execute("""
            UPDATE skills
            SET
                skill_name=%s,
                category=%s
            WHERE skill_id=%s
        """,
        (
            skill_name,
            category or None,
            skill_id
        ))

        db.commit()

        flash("Skill updated successfully.", "success")
        return redirect(url_for("admin_skills"))

    return render_template(
        "admin/edit_skill.html",
        skill=skill,
        categories=categories
    )


@app.route("/admin/delete-skill/<int:skill_id>")
@admin_required
def admin_delete_skill(skill_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT skill_name
        FROM skills
        WHERE skill_id=%s
    """, (skill_id,))

    skill = cursor.fetchone()

    if not skill:
        flash("Skill not found.", "danger")
        return redirect(url_for("admin_skills"))

    # career_skills, student_skills, progress_tracking, and
    # skill_courses rows referencing this skill all cascade-delete
    # via ON DELETE CASCADE in the schema. That means deleting a
    # skill here silently removes it from every student's skill
    # list and every career's requirements too — the confirm dialog
    # on the list page warns about this before it happens.
    cursor.execute("""
        DELETE FROM skills
        WHERE skill_id=%s
    """, (skill_id,))

    db.commit()

    flash(
        "Skill \"" + skill["skill_name"] + "\" deleted.",
        "success"
    )
    return redirect(url_for("admin_skills"))


@app.route("/admin/career-skills", methods=["GET", "POST"])
@admin_required
def career_skills_map():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT career_id, career_name
        FROM careers
        ORDER BY career_name
    """)

    careers = cursor.fetchall()

    if not careers:
        flash("Add a career first before mapping skills to it.", "danger")
        return redirect(url_for("admin_careers"))

    if request.method == "POST":

        career_id = int(request.form.get("career_id"))

        selected_skill_ids = {
            int(skill_id)
            for skill_id in request.form.getlist("skill_ids")
        }

        cursor.execute("""
            SELECT skill_id
            FROM career_skills
            WHERE career_id=%s
        """, (career_id,))

        current_skill_ids = {
            row["skill_id"]
            for row in cursor.fetchall()
        }

        to_add = selected_skill_ids - current_skill_ids
        to_remove = current_skill_ids - selected_skill_ids

        for skill_id in to_add:

            cursor.execute("""
                INSERT INTO career_skills
                (career_id, skill_id)
                VALUES (%s, %s)
            """, (career_id, skill_id))

        for skill_id in to_remove:

            cursor.execute("""
                DELETE FROM career_skills
                WHERE career_id=%s
                AND skill_id=%s
            """, (career_id, skill_id))

        db.commit()

        # The required-skill set for this career just changed, so every
        # student currently targeting it needs their roadmap (missing
        # skills / steps) recalculated to match.
        if to_add or to_remove:

            cursor.execute("""
                SELECT profile_id
                FROM student_profiles
                WHERE target_career_id=%s
            """, (career_id,))

            affected_profiles = cursor.fetchall()

            for row in affected_profiles:
                generate_learning_roadmap(row["profile_id"], career_id)

        flash("Career skill requirements updated.", "success")
        return redirect(url_for("career_skills_map", career_id=career_id))

    # =========================
    # GET
    # =========================

    selected_career_id = request.args.get("career_id", type=int)

    if not selected_career_id:
        selected_career_id = careers[0]["career_id"]

    cursor.execute("""
        SELECT career_id, career_name
        FROM careers
        WHERE career_id=%s
    """, (selected_career_id,))

    selected_career = cursor.fetchone()

    if not selected_career:
        flash("Career not found.", "danger")
        return redirect(url_for("career_skills_map"))

    # All skills, grouped by category in the template
    cursor.execute("""
        SELECT skill_id, skill_name, category
        FROM skills
        ORDER BY category, skill_name
    """)

    all_skills = cursor.fetchall()

    # Group into { category: [skills...] } while preserving order
    grouped_skills = {}

    for skill in all_skills:

        category = skill["category"] or "Uncategorized"

        if category not in grouped_skills:
            grouped_skills[category] = []

        grouped_skills[category].append(skill)

    # Currently mapped skill IDs for the selected career
    cursor.execute("""
        SELECT skill_id
        FROM career_skills
        WHERE career_id=%s
    """, (selected_career_id,))

    mapped_skill_ids = {
        row["skill_id"]
        for row in cursor.fetchall()
    }

    return render_template(
        "admin/career_skills.html",
        careers=careers,
        selected_career=selected_career,
        grouped_skills=grouped_skills,
        mapped_skill_ids=mapped_skill_ids
    )


def _grouped_skills_for_course_form():
    """
    Shared helper for add_course/edit_course — returns all skills
    grouped by category, same shape career_skills_map uses, so the
    course form can reuse the same checkbox-grid template pattern.
    """

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT skill_id, skill_name, category
        FROM skills
        ORDER BY category, skill_name
    """)

    all_skills = cursor.fetchall()

    grouped_skills = {}

    for skill in all_skills:

        category = skill["category"] or "Uncategorized"

        if category not in grouped_skills:
            grouped_skills[category] = []

        grouped_skills[category].append(skill)

    return grouped_skills


@app.route("/admin/courses")
@admin_required
def admin_courses():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            co.course_id,
            co.course_name,
            co.provider,
            co.course_link,
            co.description,

            (
                SELECT COUNT(*)
                FROM skill_courses sc
                WHERE sc.course_id = co.course_id
            ) AS skill_count

        FROM courses co

        ORDER BY co.course_name
    """)

    courses = cursor.fetchall()

    return render_template(
        "admin/courses.html",
        courses=courses
    )


@app.route("/admin/add-course", methods=["GET", "POST"])
@admin_required
def add_course():

    if request.method == "POST":

        course_name = request.form.get("course_name", "").strip()
        provider = request.form.get("provider", "").strip()
        course_link = request.form.get("course_link", "").strip()
        description = request.form.get("description", "").strip()

        selected_skill_ids = {
            int(skill_id)
            for skill_id in request.form.getlist("skill_ids")
        }

        if not course_name:
            flash("Course name is required.", "danger")
            return redirect(url_for("add_course"))

        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO courses
            (course_name, provider, course_link, description)
            VALUES (%s, %s, %s, %s)
        """,
        (
            course_name,
            provider or None,
            course_link or None,
            description or None
        ))

        db.commit()

        course_id = cursor.lastrowid

        for skill_id in selected_skill_ids:

            cursor.execute("""
                INSERT INTO skill_courses
                (skill_id, course_id)
                VALUES (%s, %s)
            """, (skill_id, course_id))

        db.commit()

        flash("Course added successfully.", "success")
        return redirect(url_for("admin_courses"))

    return render_template(
        "admin/add_course.html",
        grouped_skills=_grouped_skills_for_course_form(),
        mapped_skill_ids=set()
    )


@app.route("/admin/edit-course/<int:course_id>", methods=["GET", "POST"])
@admin_required
def edit_course(course_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM courses
        WHERE course_id=%s
    """, (course_id,))

    course = cursor.fetchone()

    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("admin_courses"))

    if request.method == "POST":

        course_name = request.form.get("course_name", "").strip()
        provider = request.form.get("provider", "").strip()
        course_link = request.form.get("course_link", "").strip()
        description = request.form.get("description", "").strip()

        selected_skill_ids = {
            int(skill_id)
            for skill_id in request.form.getlist("skill_ids")
        }

        if not course_name:
            flash("Course name is required.", "danger")
            return redirect(url_for("edit_course", course_id=course_id))

        cursor.execute("""
            UPDATE courses
            SET
                course_name=%s,
                provider=%s,
                course_link=%s,
                description=%s
            WHERE course_id=%s
        """,
        (
            course_name,
            provider or None,
            course_link or None,
            description or None,
            course_id
        ))

        cursor.execute("""
            SELECT skill_id
            FROM skill_courses
            WHERE course_id=%s
        """, (course_id,))

        current_skill_ids = {
            row["skill_id"]
            for row in cursor.fetchall()
        }

        to_add = selected_skill_ids - current_skill_ids
        to_remove = current_skill_ids - selected_skill_ids

        for skill_id in to_add:

            cursor.execute("""
                INSERT INTO skill_courses
                (skill_id, course_id)
                VALUES (%s, %s)
            """, (skill_id, course_id))

        for skill_id in to_remove:

            cursor.execute("""
                DELETE FROM skill_courses
                WHERE course_id=%s
                AND skill_id=%s
            """, (course_id, skill_id))

        db.commit()

        flash("Course updated successfully.", "success")
        return redirect(url_for("admin_courses"))

    cursor.execute("""
        SELECT skill_id
        FROM skill_courses
        WHERE course_id=%s
    """, (course_id,))

    mapped_skill_ids = {
        row["skill_id"]
        for row in cursor.fetchall()
    }

    return render_template(
        "admin/edit_course.html",
        course=course,
        grouped_skills=_grouped_skills_for_course_form(),
        mapped_skill_ids=mapped_skill_ids
    )


@app.route("/admin/delete-course/<int:course_id>")
@admin_required
def delete_course(course_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT course_name
        FROM courses
        WHERE course_id=%s
    """, (course_id,))

    course = cursor.fetchone()

    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("admin_courses"))

    # skill_courses rows for this course cascade-delete automatically
    # via ON DELETE CASCADE.
    cursor.execute("""
        DELETE FROM courses
        WHERE course_id=%s
    """, (course_id,))

    db.commit()

    flash(
        "Course \"" + course["course_name"] + "\" deleted.",
        "success"
    )
    return redirect(url_for("admin_courses"))


@app.route("/admin/students")
@admin_required
def admin_students():

    search_query = request.args.get("q", "").strip()

    cursor = db.cursor(dictionary=True)

    base_sql = """
        SELECT
            u.user_id,
            u.full_name,
            u.email,
            u.created_at,
            sp.profile_id,
            sp.university,
            sp.degree,
            sp.years_of_study,
            c.career_name,

            (
                SELECT COUNT(*)
                FROM student_skills ss
                WHERE ss.profile_id = sp.profile_id
            ) AS skill_count

        FROM users u

        JOIN student_profiles sp
        ON sp.user_id = u.user_id

        LEFT JOIN careers c
        ON sp.target_career_id = c.career_id

        WHERE u.role='student'
    """

    params = ()

    if search_query:

        base_sql += """
            AND (
                u.full_name LIKE %s
                OR u.email LIKE %s
                OR sp.university LIKE %s
            )
        """

        like_term = "%" + search_query + "%"
        params = (like_term, like_term, like_term)

    base_sql += " ORDER BY u.created_at DESC"

    cursor.execute(base_sql, params)

    students = cursor.fetchall()

    return render_template(
        "admin/students.html",
        students=students,
        search_query=search_query
    )


@app.route("/admin/student/<int:profile_id>")
@admin_required
def view_student(profile_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            u.user_id,
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

        WHERE sp.profile_id=%s
    """, (profile_id,))

    student = cursor.fetchone()

    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("admin_students"))

    # =========================
    # SKILLS
    # =========================

    cursor.execute("""
        SELECT s.skill_name, ss.proficiency_level
        FROM student_skills ss
        JOIN skills s ON s.skill_id = ss.skill_id
        WHERE ss.profile_id=%s
        ORDER BY s.skill_name
    """, (profile_id,))

    skills = cursor.fetchall()

    # =========================
    # SKILL MATCH FOR TARGET CAREER
    # =========================

    match_percentage = 0
    missing_skills = []

    if student["target_career_id"]:

        cursor.execute("""
            SELECT skill_id
            FROM career_skills
            WHERE career_id=%s
        """, (student["target_career_id"],))

        required_ids = {row["skill_id"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT skill_id
            FROM student_skills
            WHERE profile_id=%s
        """, (profile_id,))

        owned_ids = {row["skill_id"] for row in cursor.fetchall()}

        if required_ids:
            matched = required_ids.intersection(owned_ids)
            match_percentage = round((len(matched) / len(required_ids)) * 100)

        cursor.execute("""
            SELECT s.skill_name
            FROM career_skills cs
            JOIN skills s ON s.skill_id = cs.skill_id
            WHERE cs.career_id=%s
            AND cs.skill_id NOT IN (
                SELECT skill_id FROM student_skills WHERE profile_id=%s
            )
            ORDER BY s.skill_name
        """, (student["target_career_id"], profile_id))

        missing_skills = cursor.fetchall()

    # =========================
    # ROADMAP
    # =========================

    cursor.execute("""
        SELECT *
        FROM learning_roadmaps
        WHERE profile_id=%s
        ORDER BY step_no
    """, (profile_id,))

    roadmap = cursor.fetchall()

    # =========================
    # RESUME
    # =========================

    cursor.execute("""
        SELECT *
        FROM resumes
        WHERE profile_id=%s
    """, (profile_id,))

    resume = cursor.fetchone()

    return render_template(
        "admin/view_student.html",
        student=student,
        skills=skills,
        match_percentage=match_percentage,
        missing_skills=missing_skills,
        roadmap=roadmap,
        resume=resume
    )


@app.route("/admin/delete-student/<int:user_id>")
@admin_required
def delete_student(user_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT full_name, role
        FROM users
        WHERE user_id=%s
    """, (user_id,))

    user = cursor.fetchone()

    if not user:
        flash("Student not found.", "danger")
        return redirect(url_for("admin_students"))

    if user["role"] != "student":
        flash("Only student accounts can be deleted here.", "danger")
        return redirect(url_for("admin_students"))

    # Look up their profile so we can clean up files on disk before
    # the DB rows referencing them are gone — the cascade deletes
    # the DB rows, but never touches the actual files.
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

    flash(
        "Student \"" + user["full_name"] + "\" and all their data have been deleted.",
        "success"
    )
    return redirect(url_for("admin_students"))


@app.route("/admin/reports")
@admin_required
def admin_reports():

    cursor = db.cursor(dictionary=True)

    # =========================
    # STUDENTS PER CAREER
    # =========================

    cursor.execute("""
        SELECT
            c.career_name,
            COUNT(sp.profile_id) AS student_count

        FROM careers c

        LEFT JOIN student_profiles sp
        ON sp.target_career_id = c.career_id

        GROUP BY c.career_id, c.career_name

        ORDER BY student_count DESC, c.career_name ASC
    """)

    career_distribution = cursor.fetchall()

    # =========================
    # TOP MISSING SKILLS
    # (most common gaps across every student with a target career)
    # =========================

    cursor.execute("""
        SELECT
            s.skill_name,
            COUNT(*) AS missing_count

        FROM student_profiles sp

        JOIN career_skills cs
        ON cs.career_id = sp.target_career_id

        JOIN skills s
        ON s.skill_id = cs.skill_id

        WHERE sp.target_career_id IS NOT NULL

        AND cs.skill_id NOT IN (
            SELECT skill_id
            FROM student_skills
            WHERE profile_id = sp.profile_id
        )

        GROUP BY s.skill_id, s.skill_name

        ORDER BY missing_count DESC

        LIMIT 8
    """)

    top_missing_skills = cursor.fetchall()

    # =========================
    # TOP SKILLS STUDENTS ALREADY HAVE
    # =========================

    cursor.execute("""
        SELECT
            s.skill_name,
            COUNT(*) AS owned_count

        FROM student_skills ss

        JOIN skills s
        ON s.skill_id = ss.skill_id

        GROUP BY s.skill_id, s.skill_name

        ORDER BY owned_count DESC

        LIMIT 8
    """)

    top_owned_skills = cursor.fetchall()

    # =========================
    # ROADMAP COMPLETION BY CAREER
    # =========================

    cursor.execute("""
        SELECT
            c.career_name,
            COUNT(lr.roadmap_id) AS total_steps,
            SUM(CASE WHEN lr.status='Completed' THEN 1 ELSE 0 END) AS completed_steps

        FROM careers c

        LEFT JOIN learning_roadmaps lr
        ON lr.career_id = c.career_id

        GROUP BY c.career_id, c.career_name

        ORDER BY c.career_name
    """)

    roadmap_rows = cursor.fetchall()

    roadmap_by_career = []

    for row in roadmap_rows:

        total = row["total_steps"] or 0
        completed = row["completed_steps"] or 0

        percentage = 0

        if total > 0:
            percentage = round((completed / total) * 100)

        roadmap_by_career.append({
            "career_name": row["career_name"],
            "total_steps": total,
            "completed_steps": completed,
            "percentage": percentage
        })

    # =========================
    # REGISTRATION TREND (last 6 months)
    # =========================

    cursor.execute("""
        SELECT
            DATE_FORMAT(created_at, '%%Y-%%m') AS month,
            COUNT(*) AS student_count

        FROM users

        WHERE role='student'

        GROUP BY month

        ORDER BY month ASC
    """)

    registration_trend = cursor.fetchall()

    # =========================
    # RESUME UPLOAD RATE
    # =========================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role='student'
    """)
    total_students = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM resumes")
    total_resumes = cursor.fetchone()["total"]

    resume_upload_rate = 0

    if total_students > 0:
        resume_upload_rate = round((total_resumes / total_students) * 100)

    return render_template(
        "admin/reports.html",
        career_distribution=career_distribution,
        top_missing_skills=top_missing_skills,
        top_owned_skills=top_owned_skills,
        roadmap_by_career=roadmap_by_career,
        registration_trend=registration_trend,
        total_students=total_students,
        total_resumes=total_resumes,
        resume_upload_rate=resume_upload_rate
    )


@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        action = request.form.get("action")

        # =========================
        # UPDATE PROFILE INFO
        # =========================

        if action == "profile":

            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()

            if not full_name or not email:
                flash("Name and email are required.", "danger")
                return redirect(url_for("admin_settings"))

            # Prevent switching to an email already used by another account
            cursor.execute("""
                SELECT user_id
                FROM users
                WHERE email=%s
                AND user_id != %s
            """, (email, user_id))

            existing = cursor.fetchone()

            if existing:
                flash("That email is already in use by another account.", "danger")
                return redirect(url_for("admin_settings"))

            cursor.execute("""
                UPDATE users
                SET full_name=%s, email=%s
                WHERE user_id=%s
            """,
            (
                full_name,
                email,
                user_id
            ))

            db.commit()

            session["full_name"] = full_name

            flash("Profile updated successfully.", "success")
            return redirect(url_for("admin_settings"))

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
                return redirect(url_for("admin_settings"))

            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for("admin_settings"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("admin_settings"))

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
            return redirect(url_for("admin_settings"))

    cursor.execute("""
        SELECT full_name, email, created_at
        FROM users
        WHERE user_id=%s
    """, (user_id,))

    admin_user = cursor.fetchone()

    return render_template(
        "admin/settings.html",
        admin_user=admin_user
    )


@app.route("/admin/messages")
@admin_required
def admin_messages():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            message_id,
            full_name,
            email,
            subject,
            message,
            submitted_at,
            is_read
        FROM contact_messages
        ORDER BY submitted_at DESC
    """)

    messages = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM contact_messages
        WHERE is_read = 0
    """)

    unread_count = cursor.fetchone()["total"]

    return render_template(
        "admin/messages.html",
        messages=messages,
        unread_count=unread_count
    )


@app.route("/admin/message/<int:message_id>")
@admin_required
def view_message(message_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM contact_messages
        WHERE message_id=%s
    """, (message_id,))

    message = cursor.fetchone()

    if not message:
        flash("Message not found.", "danger")
        return redirect(url_for("admin_messages"))

    # Mark as read the moment an admin opens it.
    if not message["is_read"]:

        cursor.execute("""
            UPDATE contact_messages
            SET is_read = 1
            WHERE message_id=%s
        """, (message_id,))

        db.commit()

    return render_template(
        "admin/view_message.html",
        message=message
    )


@app.route("/admin/delete-message/<int:message_id>")
@admin_required
def delete_message(message_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT full_name
        FROM contact_messages
        WHERE message_id=%s
    """, (message_id,))

    message = cursor.fetchone()

    if not message:
        flash("Message not found.", "danger")
        return redirect(url_for("admin_messages"))

    cursor.execute("""
        DELETE FROM contact_messages
        WHERE message_id=%s
    """, (message_id,))

    db.commit()

    flash(
        "Message from \"" + message["full_name"] + "\" deleted.",
        "success"
    )
    return redirect(url_for("admin_messages"))