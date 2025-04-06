from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.permanent_session_lifetime = timedelta(days=30)  # Keep user logged in for 30 days if 'remember me' is checked

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")

mysql = MySQL(app)

# Gemini API Setup
if not API_KEY:
    raise ValueError("Missing API Key! Add GEMINI_API_KEY to your .env file.")
genai.configure(api_key=API_KEY)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        remember = request.form.get("remember")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session.permanent = True if remember else False
            session["email"] = email
            return redirect(url_for("index"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/index")
def index():
    if "email" in session:
        return render_template("index.html")
    else:
        return redirect(url_for("login"))

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_input = data.get("message", "")
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_input)
        return jsonify({"reply": response.text.strip()})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route('/focus')
def focus():
    return render_template('focus.html')
@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/ideaboard')
def ideaboard():
    return render_template('ideaboard.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

    

@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
