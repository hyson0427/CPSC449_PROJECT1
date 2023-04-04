# Task 1
# -Create a new Flask application and set up the necessary packages and modules
# -Create a virtual environment for the application
# -Connect your Flask with the Database ( MySQL preferably )
import pymysql
from flask import Flask, render_template

app = Flask(__name__)

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="password",
    db="449_db_project1",
    cursorclass=pymysql.cursors.DictCursor,  # type: ignore
)
cur = conn.cursor()


@app.route("/")
def hello_world():
    return "Hello World"


# Task 2 : Error Handling
# -Implement error handling for your API to ensure that it returns proper
# error messages and status codes
# -Create error handles for ex. 400, 401, 404, 500 and any other errors
# that you feel are necessary
# -Make sure that error messages are returned in a consistenet format
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