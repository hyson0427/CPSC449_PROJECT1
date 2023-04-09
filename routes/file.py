import os
import time

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required
from werkzeug.utils import secure_filename

file_blueprint = Blueprint("file", __name__, url_prefix="/file")


@file_blueprint.before_app_first_request
def initialize():
    conn = current_app.config["DB_CONN"]
    cursor = current_app.config["DB_CURSOR"]

    # Make sure that the users table exists
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    timestamp INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id))"""
    )
    conn.commit()


@file_blueprint.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    conn = current_app.config["DB_CONN"]
    cursor = current_app.config["DB_CURSOR"]

    jwt_data = get_jwt()
    user_id = jwt_data["user_id"]
    timestamp = time.time_ns()

    # Error: there was no file uploaded
    if "file" not in request.files:
        return jsonify("No file uploaded"), 400

    uploaded_file = request.files["file"]

    # Error: filename is missing
    if not uploaded_file.filename:
        return jsonify("Invalid or missing filename"), 400

    # Sanitize the filename
    user_filename = secure_filename(uploaded_file.filename)

    # Create the user's directory if it doesn't exist
    user_dir = os.path.join(current_app.config["FILE_UPLOAD_PATH"], str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    # Create a unique filename based on the current time.
    # File will be stored at <UPLOAD_FOLDER>/<user_id>/<timestamp_ns>
    # File names are stored in the database
    disk_filename = os.path.join(user_dir, str(timestamp))

    # Try to save the file to disk
    try:
        uploaded_file.save(disk_filename)
    except Exception:
        return jsonify(f"Server error while saving file {user_filename}."), 500

    # Verify that the file was saved successfully before we commit to the
    # database and return success
    if os.path.exists(disk_filename):
        cursor.execute(
            "INSERT INTO files (user_id, filename, timestamp) VALUES (%s, %s, %s)",
            (user_id, user_filename, timestamp),
        )
        conn.commit()
        return jsonify("File uploaded successfully"), 200

    # For some reason the file isn't present on disk, return an error
    return jsonify(f"Server error while saving file {user_filename}."), 500

    # if filename != '':
    #     file_ext = os.path.splitext(filename)[1]
    #     if file_ext not in app.config['UPLOAD_EXTENSIONS']:
    #         abort(400)
    #     uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    # return redirect(url_for('index'))
    # return jsonify("File uploaded successfully"), 200


@file_blueprint.route("/download/<int:user_id>/<string:timestamp>")
def download(user_id, timestamp):
    return jsonify("File not found"), 404
