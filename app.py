from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def db():
    return sqlite3.connect("database.db")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        con.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["role"] = user[4]
            return redirect("/admin" if user[4]=="admin" else "/report")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        con = db()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users VALUES (NULL,?,?,?,?)",
            (request.form["name"],
             request.form["email"],
             generate_password_hash(request.form["password"]),
             "user")
        )
        con.commit()
        con.close()
        return redirect("/")
    return render_template("register.html")

@app.route("/report", methods=["GET","POST"])
def report():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        file = request.files["evidence"]
        filename = ""
        if file:
            filename = datetime.now().strftime("%H%M%S_") + file.filename
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        con = db()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO complaints VALUES (NULL,?,?,?,?,?,?,?,?)
        """, (
            session["user_id"],
            request.form["noise_type"],
            request.form["db_level"],
            request.form["location"],
            request.form["description"],
            "Pending",
            filename,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        con.commit()
        con.close()
    return render_template("report.html")

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    data = cur.fetchall()
    con.close()
    return render_template("admin.html", data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(debug=True)
