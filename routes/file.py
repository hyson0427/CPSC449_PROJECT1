import os
import time

import pymysql.cursors
from flask import Blueprint, current_app, jsonify, request, send_from_directory
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
                    timestamp BIGINT,
                    public BOOLEAN DEFAULT FALSE,
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
    public_value = request.values.get("public", "false")  # Default to private files
    is_public = 1 if public_value.lower() == "true" else 0

    # Error: filename is missing
    if not uploaded_file.filename:
        return jsonify("Invalid or missing filename"), 400

    # Sanitize the filename
    user_filename = secure_filename(uploaded_file.filename)

    # Check if the user has already uploaded a file with this name
    if file_already_uploaded(user_id, user_filename, cursor):
        existing_timestamp = get_file_timestamp(user_id, user_filename, cursor)
        return (
            jsonify(
                f"File already uploaded. Download link: http://127.0.0.1:5000/file/download/{user_id}/{existing_timestamp}"
            ),
            400,
        )

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
            "INSERT INTO files (user_id, filename, timestamp, public) VALUES (%s, %s, %s, %s)",
            (user_id, user_filename, timestamp, is_public),
        )
        conn.commit()
        return (
            jsonify(
                f"Upload successful. Download link: http://127.0.0.1:5000/file/download/{user_id}/{timestamp}"
            ),
            200,
        )

    # For some reason the file isn't present on disk, return an error
    return jsonify(f"Server error while saving file {user_filename}."), 500


@file_blueprint.route("/download/<int:user_id>/<int:timestamp>", methods=["GET"])
def download(user_id, timestamp):
    upload_path = os.path.join(current_app.config["FILE_UPLOAD_PATH"], str(user_id))
    file_name = str(timestamp)
    full_path = os.path.join(upload_path, file_name)

    # User specified a file that doesn't exist
    if not os.path.exists(full_path):
        return jsonify("File does not exist"), 404

    # Get the original filename from the database
    cursor = current_app.config["DB_CURSOR"]
    cursor.execute(
        "SELECT filename FROM files WHERE user_id=%s AND timestamp=%s",
        (user_id, timestamp),
    )
    row = cursor.fetchone()

    # For some reason the file isn't present in the database, return an error
    if row is None:
        return jsonify("File not found in database"), 404
    user_filename = row["filename"]

    # Send the file using the original (sanitized) filename
    return send_from_directory(
        upload_path, file_name, as_attachment=True, download_name=user_filename
    )


@file_blueprint.route("/list", methods=["GET"])
def list():
    cursor = current_app.config["DB_CURSOR"]
    cursor.execute("SELECT * FROM files where public=TRUE")
    all_results = cursor.fetchall()

    if len(all_results) == 0:
        return jsonify("No public files found"), 404

    public_files = []

    for result in all_results:
        user_id = result["user_id"]
        timestamp = result["timestamp"]
        filename = result["filename"]
        url = f"http://127.0.0.1:5000/file/download/{user_id}/{timestamp}"

        file = {"filename": filename, "url": url}
        public_files.append(file)

    return jsonify(public_files), 200


def file_already_uploaded(user_id, file_name, cursor: pymysql.cursors.Cursor) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM files WHERE user_id=%s AND filename=%s",
        (user_id, file_name),
    )
    result = cursor.fetchone()
    count = result["COUNT(*)"]  # type: ignore

    # If there is a result, count is > 0
    return count > 0


def get_file_timestamp(user_id, file_name, cursor: pymysql.cursors.Cursor) -> int:
    cursor.execute(
        "SELECT timestamp FROM files WHERE user_id=%s AND filename=%s",
        (user_id, file_name),
    )
    result = cursor.fetchone()
    timestamp = result["timestamp"]  # type: ignore

    return timestamp
