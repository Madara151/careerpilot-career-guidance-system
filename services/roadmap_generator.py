from config.db import db

ROADMAP_DESCRIPTIONS = {

    "Python": "Complete a beginner Python programming course.",

    "SQL": "Learn relational databases and SQL queries.",

    "Machine Learning": "Study supervised and unsupervised learning algorithms.",

    "Statistics": "Understand descriptive and inferential statistics.",

    "Power BI": "Create dashboards using Power BI.",

    "Java": "Learn Java programming fundamentals.",

    "HTML": "Learn webpage structure using HTML.",

    "CSS": "Learn responsive web design using CSS.",

    "JavaScript": "Learn interactive web development.",

    "React": "Build modern frontend applications.",

    "Git": "Learn version control using Git.",

    "AWS": "Learn Amazon Web Services.",

    "Linux": "Learn Linux administration."

}


def generate_learning_roadmap(profile_id, career_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        roadmap_id,
        title,
        status
    FROM learning_roadmaps
    WHERE profile_id=%s
    """, (profile_id,))

    existing_steps = cursor.fetchall()

    existing_map = {}

    for step in existing_steps:

        existing_map[
            step["title"]
        ] = {

            "roadmap_id": step["roadmap_id"],
            "status": step["status"]

        }

    # Find missing skills
    cursor.execute("""
        SELECT
            s.skill_id,
            s.skill_name

        FROM career_skills cs

        JOIN skills s
        ON cs.skill_id=s.skill_id

        WHERE cs.career_id=%s

        AND s.skill_id NOT IN (

            SELECT skill_id
            FROM student_skills
            WHERE profile_id=%s

        )

        ORDER BY s.skill_name
    """, (career_id, profile_id))

    missing_skills = cursor.fetchall()

    current_titles = []

    step = 1

    for skill in missing_skills:

        title = "Learn " + skill["skill_name"]

        current_titles.append(title)

        description = ROADMAP_DESCRIPTIONS.get(
            skill["skill_name"],
            "Complete this skill."
        )

        if title in existing_map:

            cursor.execute("""
                UPDATE learning_roadmaps

                SET

                step_no=%s,
                description=%s

                WHERE roadmap_id=%s
            """,
            (
                step,
                description,
                existing_map[title]["roadmap_id"]
            ))

        else:

            cursor.execute("""
                INSERT INTO learning_roadmaps
                (
                    career_id,
                    profile_id,
                    step_no,
                    title,
                    description,
                    status
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """,
            (
                career_id,
                profile_id,
                step,
                title,
                description,
                "Not Started"
            ))

        step += 1

    # FIX: this cleanup used to be nested inside the "for skill in
    # missing_skills" loop above, which made it re-run once per skill and
    # compare against a partially-built current_titles list. It now runs
    # once, after current_titles is fully built, so stale roadmap steps
    # (skills the student already learned / no longer needs) are removed
    # correctly instead of sometimes surviving or being deleted too early.
    for title in existing_map:

        if title not in current_titles:

            cursor.execute("""
                DELETE
                FROM learning_roadmaps
                WHERE roadmap_id=%s
            """,
            (
                existing_map[title]["roadmap_id"],
            ))

    db.commit()
