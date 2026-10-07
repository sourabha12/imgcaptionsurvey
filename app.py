from flask import Flask, render_template, jsonify, request, send_from_directory
from pathlib import Path
import sqlite3
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# PATHS
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent

SURVEY_DIR = BASE_DIR / "survey_data"
IMAGE_DIR = SURVEY_DIR / "images"
CAPTION_FILE = SURVEY_DIR / "captions.txt"

DB_FILE = BASE_DIR / "survey.db"


# -----------------------------
# LOAD IMAGES
# -----------------------------

images = {}

for image in IMAGE_DIR.glob("*.jpg"):
    images[image.name] = image

print("Images found:", len(images))


# -----------------------------
# LOAD CAPTIONS
# -----------------------------

captions = {}

if CAPTION_FILE.exists():

    with open(CAPTION_FILE, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            parts = line.split("|", 1)

            if len(parts) == 2:

                image_name = parts[0]
                caption = parts[1]

                captions[image_name] = caption


# -----------------------------
# SELECT AVAILABLE IMAGES
# -----------------------------

selected_images = []

for image_name in captions:

    if image_name in images:

        selected_images.append(image_name)


print("Survey images:", len(selected_images))


# -----------------------------
# DATABASE
# -----------------------------

def init_database():

    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            participant_name TEXT NOT NULL,

            gmail TEXT NOT NULL,

            image TEXT NOT NULL,

            caption TEXT NOT NULL,

            accuracy INTEGER,
            relevance INTEGER,
            fluency INTEGER,
            detail INTEGER,
            overall INTEGER,

            submitted_at TEXT

        )
    """)

    connection.commit()

    connection.close()


init_database()


# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------
# SEND SURVEY DATA
# -----------------------------

@app.route("/survey_data")
def survey_data():

    data = []

    for image_name in selected_images:

        data.append({

            "image": "/image/" + image_name,

            "filename": image_name,

            "caption": captions[image_name]

        })

    return jsonify(data)


# -----------------------------
# DISPLAY IMAGE
# -----------------------------

@app.route("/image/<filename>")
def show_image(filename):

    if filename not in images:

        return "Image not found", 404

    return send_from_directory(
        IMAGE_DIR,
        filename
    )


# -----------------------------
# SAVE SURVEY
# -----------------------------

@app.route("/submit", methods=["POST"])
def submit():

    data = request.json

    name = data.get("name")
    gmail = data.get("gmail")
    responses = data.get("responses")

    if not name or not gmail:

        return jsonify({

            "success": False,

            "message": "Name and Gmail are required."

        }), 400


    connection = sqlite3.connect(DB_FILE)

    cursor = connection.cursor()


    for response in responses:

        cursor.execute("""

            INSERT INTO responses

            (
                participant_name,
                gmail,
                image,
                caption,
                accuracy,
                relevance,
                fluency,
                detail,
                overall,
                submitted_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            name,

            gmail,

            response["image"],

            response["caption"],

            response["accuracy"],

            response["relevance"],

            response["fluency"],

            response["detail"],

            response["overall"],

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ))


    connection.commit()

    connection.close()


    return jsonify({

        "success": True

    })


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
