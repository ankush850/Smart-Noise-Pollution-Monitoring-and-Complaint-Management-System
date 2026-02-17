from flask import Flask, render_template, request, redirect, session, flash, url_for, g
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-123")
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = "database.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("admin" if session["role"] == "admin" else "report"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("admin" if user["role"] == "admin" else "report"))
        else:
            flash("Invalid email or password.", "error")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, generate_password_hash(password), "user")
            )
            db.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
            
    return render_template("register.html")

@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    if request.method == "POST":
        noise_type = request.form.get("noise_type")
        db_level = request.form.get("db_level")
        location = request.form.get("location")
        description = request.form.get("description")
        file = request.files.get("evidence")
        
        filename = ""
        if file and file.filename != "":
            filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + file.filename
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        db = get_db()
        db.execute("""
            INSERT INTO complaints (user_id, noise_type, db_level, location, description, status, evidence, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            noise_type,
            db_level,
            location,
            description,
            "Pending",
            filename,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        db.commit()
        flash("Your complaint has been submitted successfully.", "success")
        return redirect(url_for("report"))

    return render_template("report.html")

@app.route("/my-reports")
@login_required
def my_reports():
    if session.get("role") == "admin":
        return redirect(url_for("admin"))
    
    db = get_db()
    complaints = db.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    return render_template("my_reports.html", complaints=complaints)

@app.route("/admin")
@login_required
def admin():
    if session.get("role") != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for("report"))

    db = get_db()
    # Join with users table to get the reporter's name
    complaints = db.execute("""
        SELECT c.*, u.name as user_name 
        FROM complaints c 
        JOIN users u ON c.user_id = u.id 
        ORDER BY c.id DESC
    """).fetchall()

    # Get stats for charts
    stats_by_type = db.execute("SELECT noise_type, COUNT(*) as count FROM complaints GROUP BY noise_type").fetchall()
    stats_by_status = db.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status").fetchall()
    
    return render_template("admin.html", 
                         complaints=complaints, 
                         stats_by_type=stats_by_type,
                         stats_by_status=stats_by_status)

@app.route("/admin/export")
@login_required
def export_csv():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    
    import csv
    from io import StringIO
    from flask import make_response

    db = get_db()
    complaints = db.execute("""
        SELECT c.id, u.name, c.noise_type, c.db_level, c.location, c.status, c.date 
        FROM complaints c JOIN users u ON c.user_id = u.id
    """).fetchall()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Reporter', 'Type', 'DB Level', 'Location', 'Status', 'Date'])
    for row in complaints:
        cw.writerow(list(row))

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=noise_reports.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route("/api/v1/report", methods=["POST"])
def api_report():
    # Basic API for IoT devices
    api_key = request.headers.get("X-API-KEY")
    if api_key != "noise-sensor-secret-2026":
        return {"error": "Unauthorized"}, 401
    
    data = request.get_json()
    db = get_db()
    db.execute("""
        INSERT INTO complaints (user_id, noise_type, db_level, location, description, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        1, # Default system user
        data.get("type", "Sensor Alert"),
        data.get("db_level"),
        data.get("location"),
        data.get("description", "Automated sensor report"),
        "Pending",
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    db.commit()
    return {"status": "success"}, 201

@app.route("/admin/update_status/<int:complaint_id>", methods=["POST"])
@login_required
def update_status(complaint_id):
    if session.get("role") != "admin":
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {"error": "Unauthorized"}, 401
        return redirect(url_for("login"))
    
    status = request.form.get("status")
    db = get_db()
    db.execute("UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
    db.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"status": "success", "message": f"Complaint #{complaint_id} updated to {status}"}
    
    flash(f"Complaint #{complaint_id} status updated to {status}.", "success")
    return redirect(url_for("admin"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        db.execute("UPDATE users SET name=?, email=? WHERE id=?", (name, email, session["user_id"]))
        db.commit()
        session["user_name"] = name
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
