import pymysql.cursors
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token

auth_blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@auth_blueprint.before_app_first_request
def initialize():
    conn = current_app.config["DB_CONN"]
    cursor = current_app.config["DB_CURSOR"]

    # Make sure that the users table exists
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
                    username TEXT,
                    password TEXT)"""
    )
    conn.commit()


@auth_blueprint.route("/login", methods=["POST"])
def login():
    cursor = current_app.config["DB_CURSOR"]

    if not request.is_json or not request.json:
        return jsonify({"msg": "JSON is missing or invalid."}), 400

    username = request.json.get("username")
    password = request.json.get("password")

    # Missing username/password
    if not username or not password:
        return jsonify({"msg": "Username or password is missing."}), 400

    # Check if the user exists
    if not user_exists(username, cursor):
        return jsonify({"msg": "User does not exist."}), 400

    # Check if the password is correct
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    bcrypt = current_app.config["BCRYPT"]
    if not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"msg": "Incorrect password."}), 400

    # Generate and return the JWT token
    jwt_token = create_access_token(identity=username)
    return jsonify({"access_token": jwt_token}), 200


@auth_blueprint.route("/register", methods=["POST"])
def register():
    cursor = current_app.config["DB_CURSOR"]
    conn = current_app.config["DB_CONN"]

    if not request.is_json or not request.json:
        return jsonify({"msg": "JSON is missing or invalid."}), 400

    username = request.json.get("username")
    password = request.json.get("password")

    # Missing username/password
    if not username or not password:
        return jsonify({"msg": "Username or password is missing."}), 400

    # User already exists
    if user_exists(username, cursor):
        return jsonify({"msg": "User already exists."}), 400

    # Hash the password with bcrypt
    bcrypt = current_app.config["BCRYPT"]
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Insert the user into the database
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed_password),
    )
    conn.commit()

    # Generate and return the JWT token
    jwt_token = create_access_token(identity=username)
    return jsonify({"access_token": jwt_token}), 201


def user_exists(username: str, cursor: pymysql.cursors.Cursor) -> bool:
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    return cursor.fetchone() is not None
