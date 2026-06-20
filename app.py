
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import mysql.connector
from datetime import datetime, date
import base64

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Dhanu@26",
        database="vms_db"
    )


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            visitor_id VARCHAR(50) UNIQUE,
            name VARCHAR(150) NOT NULL,
            mobile VARCHAR(20),
            email VARCHAR(150),
            gender VARCHAR(50),
            dob VARCHAR(50),
            visitor_type VARCHAR(100),
            company VARCHAR(150),
            purpose VARCHAR(150),
            purpose_details TEXT,
            department VARCHAR(150),
            host VARCHAR(150),
            visit_date DATE,
            visit_time VARCHAR(50),
            address TEXT,
            emergency_contact VARCHAR(20),
            vehicle_number VARCHAR(50),
            status VARCHAR(50) DEFAULT 'Pending Check-In',
            registration_time DATETIME,
            checkin_time DATETIME NULL,
            checkout_time DATETIME NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------
@app.route('/')
def login():
    return render_template("login.html")


# ---------------- AUTH ----------------
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM users
        WHERE username=%s AND password=%s
    """, (username, password))

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "message": "Login Success",
            "role": user["role"]
        })

    return jsonify({"message": "Invalid Credentials"}), 401


# ---------------- ROLE ROUTES ----------------
@app.route('/admin')
def admin():
    return redirect(url_for("dashboard"))


@app.route('/reception')
def reception():
    return redirect(url_for("dashboard"))


@app.route('/employee')
def employee():
    return redirect(url_for("dashboard"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM visitors")
    total_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Pending Check-In'")
    pending_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Checked In'")
    checked_in_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Checked Out'")
    checked_out_visitors = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT *
        FROM visitors
        ORDER BY id DESC
        LIMIT 5
    """)
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        "UPDATE visitors SET visitor_id=%s WHERE id=%s",
        (visitor_id, visitor_db_id)
    )

    conn.commit()
    conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    visitor = cursor.fetchone()

    conn.close()

    return render_template(
        "success.html",
        visitor=visitor,
        image_data=image_data
    )


# ---------------- SUCCESS PAGE ----------------
@app.route("/registration_success/<visitor_id>")
def registration_success(visitor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM visitors WHERE visitor_id=%s", (visitor_id,))
    visitor = cursor.fetchone()

    conn.close()

    if not visitor:
        return "Visitor not found", 404

    return render_template("success.html", visitor=visitor, image_data=None)


# ---------------- CHECKIN / CHECKOUT ----------------
@app.route("/checkin_checkout")
def checkin_checkout():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM visitors ORDER BY id DESC")
    visitors = cursor.fetchall()

    conn.close()

    return render_template("checkin_checkout.html", visitors=visitors)


@app.route("/checkin")
def checkin():
    return redirect(url_for("checkin_checkout"))


@app.route("/history")
def history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM visitors ORDER BY id DESC")
    visitors = cursor.fetchall()

    conn.close()

    return render_template("history.html", visitors=visitors)


@app.route("/reports")
def reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    today = date.today().strftime("%Y-%m-%d")

    cursor.execute("SELECT COUNT(*) AS total FROM visitors")
    total_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Pending Check-In'")
    pending_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Checked In'")
    checked_in_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Checked Out'")
    checked_out_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE visit_date=%s", (today,))
    daily_visitors = cursor.fetchone()["total"]

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


@app.route("/logout")
def logout():
    return redirect(url_for("login"))


# ---------------- API ROUTES ----------------
@app.route("/api/dashboard-stats")
def dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM visitors")
    total_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Pending Check-In'")
    pending_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Checked In'")
    checked_in_visitors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM visitors WHERE status='Checked Out'")
    checked_out_visitors = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "total_visitors": total_visitors,
        "pending_visitors": pending_visitors,
        "checked_in_visitors": checked_in_visitors,
        "checked_out_visitors": checked_out_visitors
    })


@app.route("/api/checkin/<int:visitor_id>", methods=["POST"])
def api_checkin(visitor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM visitors WHERE id=%s", (visitor_id,))
    visitor = cursor.fetchone()

    if not visitor:
        conn.close()
        return jsonify({"message": "Visitor not found"}), 404

    if visitor["status"] != "Pending Check-In":
        conn.close()
        return jsonify({"message": "Only Pending Check-In visitors allowed"}), 400

    checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE visitors
        SET status='Checked In', checkin_time=%s
        WHERE id=%s
    """, (checkin_time, visitor_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Checked In", "checkin_time": checkin_time})


@app.route("/api/checkout/<int:visitor_id>", methods=["POST"])
def api_checkout(visitor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM visitors WHERE id=%s", (visitor_id,))
    visitor = cursor.fetchone()

    if not visitor:
        conn.close()
        return jsonify({"message": "Visitor not found"}), 404

    if visitor["status"] != "Checked In":
        conn.close()
        return jsonify({"message": "Only Checked In allowed"}), 400

    checkout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE visitors
        SET status='Checked Out', checkout_time=%s
        WHERE id=%s
    """, (checkout_time, visitor_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Checked Out", "checkout_time": checkout_time})


# ---------------- START ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
