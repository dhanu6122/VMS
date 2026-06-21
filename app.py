from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from datetime import datetime, date
import base64
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# ---------------- DATABASE ----------------
DB_NAME = "vms.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()


    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'employee'
        )
    """)

    # VISITORS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_id TEXT UNIQUE,
            name TEXT NOT NULL,
            mobile TEXT,
            email TEXT,
            gender TEXT,
            dob TEXT,
            visitor_type TEXT,
            company TEXT,
            purpose TEXT,
            purpose_details TEXT,
            department TEXT,
            host TEXT,
            visit_date TEXT,
            visit_time TEXT,
            address TEXT,
            emergency_contact TEXT,
            vehicle_number TEXT,
            status TEXT DEFAULT 'Pending Check-In',
            registration_time TEXT,
            checkin_time TEXT,
            checkout_time TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
user = cursor.fetchone()

if not user:
    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, ("admin", "admin123", "ADMIN"))

    conn.commit()

conn.close()

# ---------------- HOME ----------------
@app.route('/')
def login():
    return render_template("login.html")


# ---------------- LOGIN API ----------------
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users
    WHERE username=? AND password=?
    """, (username.strip(), password.strip()))

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "message": "Login Success",
            "role": user["role"]
        })

    return jsonify({"message": "Invalid Credentials"}), 401


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM visitors")
    total_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE status='Pending Check-In'")
    pending_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE status='Checked In'")
    checked_in_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE status='Checked Out'")
    checked_out_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM visitors ORDER BY id DESC LIMIT 5")
    recent_visitors = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_visitors=total_visitors,
        pending_visitors=pending_visitors,
        checked_in_visitors=checked_in_visitors,
        checked_out_visitors=checked_out_visitors,
        recent_visitors=recent_visitors
    )


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    file = request.files.get("image") or request.files.get("photoUpload")

    image_data = None
    if file and file.filename != "":
        image_data = base64.b64encode(file.read()).decode("utf-8")

    visitor_name = request.form.get("visitorName", "")
    mobile = request.form.get("mobile", "")
    email = request.form.get("email", "")
    gender = request.form.get("gender", "")
    dob = request.form.get("dob", "")
    visitor_type = request.form.get("visitorType", "")
    company = request.form.get("company", "") or request.form.get("companyName", "")
    purpose = request.form.get("purposeSelect", "")
    purpose_details = request.form.get("purpose", "")
    department = request.form.get("department", "")
    host = request.form.get("host", "")
    visit_date = request.form.get("visitDate", "")
    visit_time = request.form.get("visitTime", "")
    address = request.form.get("address", "")
    emergency = request.form.get("emergency", "")
    vehicle = request.form.get("vehicle", "")

    registration_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO visitors (
            name, mobile, email, gender, dob,
            visitor_type, company, purpose, purpose_details,
            department, host, visit_date, visit_time,
            address, emergency_contact, vehicle_number,
            status, registration_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        visitor_name, mobile, email, gender, dob,
        visitor_type, company, purpose, purpose_details,
        department, host, visit_date, visit_time,
        address, emergency, vehicle,
        "Pending Check-In", registration_time
    ))

    visitor_db_id = cursor.lastrowid
    visitor_id = f"VMS-{visitor_db_id:04d}"

    cursor.execute(
        "UPDATE visitors SET visitor_id=? WHERE id=?",
        (visitor_id, visitor_db_id)
    )

    conn.commit()

    cursor.execute("SELECT * FROM visitors WHERE visitor_id=?", (visitor_id,))
    visitor = cursor.fetchone()
    conn.close()

    return render_template("success.html", visitor=visitor, image_data=image_data)


# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM visitors ORDER BY id DESC")
    visitors = cursor.fetchall()

    conn.close()
    return render_template("history.html", visitors=visitors)


# ---------------- CHECKIN/OUT PAGE ----------------
@app.route("/checkin_checkout")
def checkin_checkout():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM visitors ORDER BY id DESC")
    visitors = cursor.fetchall()

    conn.close()
    return render_template("checkin_checkout.html", visitors=visitors)


# ---------------- REPORTS ----------------
@app.route("/reports")
def reports():
    conn = get_db_connection()
    cursor = conn.cursor()

    today = date.today().strftime("%Y-%m-%d")

    cursor.execute("SELECT COUNT(*) FROM visitors")
    total_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE status='Pending Check-In'")
    pending_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE status='Checked In'")
    checked_in_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE status='Checked Out'")
    checked_out_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visitors WHERE visit_date=?", (today,))
    daily_visitors = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM visitors ORDER BY id DESC")
    visitors = cursor.fetchall()

    conn.close()

    return render_template(
        "reports.html",
        visitors=visitors,
        total_visitors=total_visitors,
        pending_visitors=pending_visitors,
        checked_in_visitors=checked_in_visitors,
        checked_out_visitors=checked_out_visitors,
        daily_visitors=daily_visitors,
        today=today
    )


# ---------------- API CHECKIN ----------------
@app.route("/api/checkin/<int:visitor_id>", methods=["POST"])
def api_checkin(visitor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM visitors WHERE id=?", (visitor_id,))
    visitor = cursor.fetchone()

    if not visitor:
        return jsonify({"message": "Visitor not found"}), 404

    if visitor["status"] != "Pending Check-In":
        return jsonify({"message": "Only Pending Check-In allowed"}), 400

    checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE visitors
        SET status='Checked In', checkin_time=?
        WHERE id=?
    """, (checkin_time, visitor_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Checked In", "checkin_time": checkin_time})


# ---------------- API CHECKOUT ----------------
@app.route("/api/checkout/<int:visitor_id>", methods=["POST"])
def api_checkout(visitor_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM visitors WHERE id=?", (visitor_id,))
    visitor = cursor.fetchone()

    if not visitor:
        return jsonify({"message": "Visitor not found"}), 404

    if visitor["status"] != "Checked In":
        return jsonify({"message": "Only Checked In allowed"}), 400

    checkout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE visitors
        SET status='Checked Out', checkout_time=?
        WHERE id=?
    """, (checkout_time, visitor_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Checked Out", "checkout_time": checkout_time})


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# ---------------- START ----------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)