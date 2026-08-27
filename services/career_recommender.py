"""
Career Recommendation Engine
=============================

Ranks every career in the system by how well it matches a student's
current skill set, using TF-IDF (Term Frequency-Inverse Document
Frequency) vectorization and cosine similarity — a standard technique
from information retrieval and recommender systems.

How it works:
1. Each career's required skills, and the student's owned skills, are
   treated as "documents" (a career whose required skills are
   [Python, SQL, Git] becomes the document "Python SQL Git").
2. TF-IDF converts these documents into weighted numeric vectors —
   skills that are rarer across all careers get weighted more heavily
   than skills that appear in almost every career, so common baseline
   skills (e.g. "Git") don't dominate the match the way a rare,
   distinguishing skill (e.g. "Machine Learning") should.
3. Cosine similarity measures the angle between the student's vector
   and each career's vector — 1.0 means identical skill sets, 0.0
   means no overlap at all.

This is computed live on every request from the current database
state — there's no training step and no persisted model, so it always
reflects the latest skills/careers data with zero staleness.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _tokenize_skill(skill_name):
    """
    Turns a multi-word skill name into a single token so TF-IDF treats
    it atomically instead of splitting on spaces. Without this,
    "Machine Learning" and "Deep Learning" would partially match on
    the shared word "Learning" alone, which isn't the intent — a
    skill either matches or it doesn't.
    """

    return skill_name.strip().lower().replace(" ", "_").replace("/", "_")


def get_career_recommendations(student_skill_names, careers_with_skills):
    """
    student_skill_names: list[str] — skill names the student currently owns.

    careers_with_skills: list[dict] — one entry per career, each shaped like:
        {
            "career_id": int,
            "career_name": str,
            "description": str | None,
            "skills": list[str]   # required skill names for this career
        }

    Returns a list of dicts, sorted by similarity descending:
        {
            "career_id": int,
            "career_name": str,
            "description": str | None,
            "similarity": int (0-100),
            "required_skill_count": int
        }
    """

    # No skills yet — every career is an equally uninformed 0% match.
    # Returning early here also avoids feeding TF-IDF an empty
    # document, which would raise a ValueError.
    if not student_skill_names:

        return sorted(
            [
                {
                    "career_id": career["career_id"],
                    "career_name": career["career_name"],
                    "description": career.get("description"),
                    "similarity": 0,
                    "required_skill_count": len(career["skills"])
                }
                for career in careers_with_skills
            ],
            key=lambda c: c["career_name"]
        )

    student_document = " ".join(
        _tokenize_skill(skill) for skill in student_skill_names
    )

    career_documents = [
        " ".join(_tokenize_skill(skill) for skill in career["skills"])
        for career in careers_with_skills
    ]

    # The student's document goes first so we can slice it back out
    # after vectorizing everything together — TF-IDF weights depend
    # on the whole corpus, so student and careers must be fit jointly.
    all_documents = [student_document] + career_documents

    vectorizer = TfidfVectorizer()

    try:
        tfidf_matrix = vectorizer.fit_transform(all_documents)
    except ValueError:
        # Every document was empty (e.g. no careers have any skills
        # mapped yet) — nothing to compare, so fall back to all zeros.
        return sorted(
            [
                {
                    "career_id": career["career_id"],
                    "career_name": career["career_name"],
                    "description": career.get("description"),
                    "similarity": 0,
                    "required_skill_count": len(career["skills"])
                }
                for career in careers_with_skills
            ],
            key=lambda c: c["career_name"]
        )

    student_vector = tfidf_matrix[0:1]
    career_vectors = tfidf_matrix[1:]

    similarity_scores = cosine_similarity(student_vector, career_vectors)[0]

    results = []

    for index, career in enumerate(careers_with_skills):

        score = similarity_scores[index]

        # A career with zero mapped skills produces a zero vector,
        # which cosine_similarity can turn into NaN (0/0) rather than 0.
        if score != score:  # NaN check without importing math
            score = 0.0

        results.append({
            "career_id": career["career_id"],
            "career_name": career["career_name"],
            "description": career.get("description"),
            "similarity": round(score * 100),
            "required_skill_count": len(career["skills"])
        })

    results.sort(key=lambda c: c["similarity"], reverse=True)

    return results