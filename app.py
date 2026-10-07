from flask import Flask, render_template, jsonify, request
from pathlib import Path
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# PATHS
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "Flickr8k_Dataset"

# Automatically find files
caption_files = list(DATASET_DIR.rglob("Flickr8k.token.txt"))
image_files = list(DATASET_DIR.rglob("*.jpg"))

if not caption_files:
    print("ERROR: Flickr8k.token.txt not found")
    CAPTION_FILE = None
else:
    CAPTION_FILE = caption_files[0]

print("Caption file:", CAPTION_FILE)
print("Images found:", len(image_files))


# -----------------------------
# LOAD IMAGES
# -----------------------------

images = {}

for image in image_files:
    images[image.name] = image


# -----------------------------
# LOAD CAPTIONS
# -----------------------------

captions = {}

if CAPTION_FILE:

    with open(CAPTION_FILE, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            parts = line.split(" ", 1)

            if len(parts) == 2:

                image_id = parts[0]
                caption = parts[1]

                image_name = image_id.split("#")[0]

                if image_name not in captions:
                    captions[image_name] = []

                captions[image_name].append(caption)


# -----------------------------
# FIND MATCHING IMAGES
# -----------------------------

available_images = []

for image_name in captions:

    if image_name in images:
        available_images.append(image_name)


print("Matching images:", len(available_images))


# -----------------------------
# SELECT ONLY 20 IMAGES
# -----------------------------

if len(available_images) >= 20:

    selected_images = random.sample(available_images, 20)

else:

    selected_images = available_images


print("Survey images:", len(selected_images))


# -----------------------------
# DATABASE
# -----------------------------

DB_FILE = BASE_DIR / "survey.db"


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
# SEND 20 IMAGES TO SURVEY
# -----------------------------

@app.route("/survey_data")
def survey_data():

    data = []

    for image_name in selected_images:

        data.append({
            "image": "/image/" + image_name,
            "filename": image_name,
            "caption": captions[image_name][0]
        })

    return jsonify(data)


# -----------------------------
# DISPLAY IMAGE
# -----------------------------

@app.route("/image/<filename>")
def show_image(filename):

    if filename not in images:
        return "Image not found", 404

    image_path = images[filename]

    return image_path.read_bytes(), 200, {
        "Content-Type": "image/jpeg"
    }


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