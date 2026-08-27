import os

from flask import Flask

app = Flask(__name__)

UPLOAD_FOLDER = "uploads/resumes"
PROFILE_UPLOAD_FOLDER = "static/uploads/profile_pics"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROFILE_UPLOAD_FOLDER"] = PROFILE_UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

app.secret_key = "careerpilot_secret_key"

# Make sure upload directories exist so file.save() doesn't fail
# on a fresh checkout of the project.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROFILE_UPLOAD_FOLDER, exist_ok=True)

# Routes are registered by importing these modules.
# auth.py must be imported before student.py since student.py
# assumes the user is already authenticated via session set in auth.py.
from routes.auth import *
from routes.student import *
from routes.admin import *

if __name__ == "__main__":
    app.run(debug=True)
