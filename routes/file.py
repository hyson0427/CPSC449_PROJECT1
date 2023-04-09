from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required

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
    # uploaded_file = request.files['file']
    # filename = secure_filename(uploaded_file.filename)
    # if filename != '':
    #     file_ext = os.path.splitext(filename)[1]
    #     if file_ext not in app.config['UPLOAD_EXTENSIONS']:
    #         abort(400)
    #     uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    # return redirect(url_for('index'))
    return jsonify("File uploaded successfully"), 200


@file_blueprint.route("/download/<int:user_id>/<string:timestamp>")
def download(user_id, timestamp):
    return jsonify("File not found"), 404
