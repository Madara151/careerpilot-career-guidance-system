# CareerPilot

CareerPilot is a web-based career guidance and skill development platform built with Flask and MySQL. It helps students identify suitable career paths, understand their skill gaps, discover relevant learning resources, and track progress toward a selected career.

## Features

### Student Module
- Student registration and login
- Personal profile management
- Skill management
- Career selection
- Career recommendations based on current skills
- Career match scoring
- Skill gap analysis
- Personalized learning roadmap
- Recommended courses for missing skills
- Resume upload and management
- Progress tracking
- Account and password settings

### Admin Module
- Admin authentication and dashboard
- Student management
- Career management
- Skill management
- Course management
- Career-to-skill mapping
- Skill-to-course mapping
- Contact message management
- Student/profile viewing
- Reports and system statistics
- Admin settings

### Recommendation System
CareerPilot calculates career compatibility using:
- TF-IDF vectorization
- Cosine similarity

Student skills and each career's required skills are converted into weighted vectors, and the similarity score is used to rank career recommendations.

### Learning Roadmap
For the selected target career, the system:
1. Finds the skills required by the career.
2. Compares them with the student's existing skills.
3. Identifies missing skills.
4. Generates roadmap steps for those missing skills.
5. Keeps roadmap progress synchronized as the student's skills change.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Database | MySQL / MariaDB |
| Database Connector | `mysql-connector-python` |
| Recommendation | scikit-learn (TF-IDF, cosine similarity) |
| Resume Processing | pdfplumber |
| Data Processing | NumPy, Pandas / Python ecosystem |
| Web Server | Flask development server |

## Project Structure

```text
CareerPilot/
│
├── app.py
├── requirements.txt
│
├── config/
│   ├── __init__.py
│   └── db.py
│
├── routes/
│   ├── auth.py
│   ├── student.py
│   └── admin.py
│
├── services/
│   ├── career_recommender.py
│   ├── recommendation_engine.py
│   ├── resume_parser.py
│   ├── roadmap_generator.py
│   └── skill_matcher.py
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
│
├── templates/
│   ├── public/
│   ├── student/
│   └── admin/
│
└── uploads/
    └── resumes/
```

## Database

The repository includes a MySQL/MariaDB database dump:

```text
careerpilot.sql
```

The database contains the following main tables:

```text
users
student_profiles
skills
student_skills
careers
career_skills
courses
skill_courses
resumes
learning_roadmaps
progress_tracking
contact_messages
```

## Requirements

- Python 3.11+ recommended
- MySQL or MariaDB
- pip
- Git

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/careerpilot-career-guidance-system.git
cd careerpilot-career-guidance-system
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> If the repository's `requirements.txt` has encoding issues on your machine, save it as UTF-8 before installing.

### 4. Create the database

Start MySQL/MariaDB and create the database:

```sql
CREATE DATABASE careerpilot;
```

Import the provided SQL dump:

```bash
mysql -u root -p careerpilot < careerpilot.sql
```

Or import `careerpilot.sql` through phpMyAdmin.

### 5. Configure the database connection

Update:

```text
config/db.py
```

with your local MySQL credentials.

Example:

```python
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="careerpilot"
)

cursor = db.cursor()
```

### 6. Configure the Flask secret key

Do not use the development secret key in a public repository. Replace it with a secure value and preferably load it from an environment variable.

Example:

```python
import os

app.secret_key = os.environ.get("SECRET_KEY")
```

### 7. Run the application

```bash
python app.py
```

The application will normally be available at:

```text
http://127.0.0.1:5000
```

## Application Flow

```text
Student Registration / Login
            │
            ▼
      Student Profile
            │
            ▼
       Add Skills
            │
            ▼
   Career Recommendation
      (TF-IDF + Cosine)
            │
            ▼
    Select Target Career
            │
            ├───────────────┐
            ▼               ▼
     Skill Gap Analysis   Recommended Courses
            │
            ▼
     Learning Roadmap
            │
            ▼
     Progress Tracking
```

## Recommendation Logic

The recommendation engine treats the student's skill set and each career's required skills as text documents.

For each skill:

```text
"Machine Learning"
```

is normalized into an atomic token:

```text
machine_learning
```

This prevents multi-word skills from being incorrectly matched only because they share common words.

The system then:

1. Builds TF-IDF vectors for the student and all careers.
2. Calculates cosine similarity between the student vector and each career vector.
3. Converts the similarity value into a percentage score.
4. Sorts careers from highest match to lowest match.

The recommendation is calculated from the current database state rather than relying on a separately trained model.

## Resume Processing

Students can upload resumes in PDF format. The system stores resume information and provides resume management functionality within the student dashboard.

## Security Notes

Before publishing this project publicly, remove or replace all sensitive and personal data from the repository.

Do **not** commit:
- Real user names, email addresses, or contact messages
- Uploaded student profile pictures
- Uploaded resumes
- Database passwords
- Flask secret keys
- Other credentials or private configuration values
- Python `__pycache__` directories

Use environment variables for secrets and database credentials in production.

## Development Notes

This project is designed as a full-stack academic/software engineering project demonstrating:
- MVC-style Flask organization
- Relational database design
- Authentication and role-based access
- Recommendation-system concepts
- Skill matching
- File upload handling
- Dynamic learning-roadmap generation
- CRUD-based administration

## Future Improvements

Potential improvements include:
- More sophisticated career recommendation models
- Larger and regularly updated career/skill datasets
- Resume-to-skill extraction
- External course API integration
- JWT or OAuth-based authentication
- Stronger input validation and CSRF protection
- Production deployment with Gunicorn/Nginx
- Environment-based configuration
- Automated testing and CI/CD

