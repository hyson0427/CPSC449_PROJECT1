# Task 1
# -Create a new Flask application and set up the necessary packages and modules
# -Create a virtual environment for the application
# -Connect your Flask with the Database ( MySQL preferably )
import pymysql
from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from db_config import MYSQL_DB, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_USER
from jwt_config import JWT_SECRET_KEY
from routes.auth import auth_blueprint

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# Initialize and store bcrypt
bcrypt = Bcrypt(app)
app.config["BCRYPT"] = bcrypt

conn = pymysql.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    db=MYSQL_DB,
    cursorclass=pymysql.cursors.DictCursor,  # type: ignore
)
curr = conn.cursor()

# Register the DB in app.config so we can use it in blueprints
app.config["DB_CONN"] = conn
app.config["DB_CURSOR"] = curr

# Register all blueprints
app.register_blueprint(auth_blueprint)


@app.route("/")
def hello_world():
    return "Hello World"


# Task 2 : Error Handling
# -Implement error handling for your API to ensure that it returns proper
# error messages and status codes
# -Create error handles for ex. 400, 401, 404, 500 and any other errors
# that you feel are necessary
# -Make sure that error messages are returned in a consistent format
@app.errorhandler(400)
def bad_request(e):
    return render_template("400.html"), 400


@app.errorhandler(401)
def unauthorized(e):
    return render_template("401.html"), 401


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(host="localhost", port=int("5000"))
