from flask import Flask, request, jsonify, render_template
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask import Flask, render_template, request, redirect, url_for, session

import uuid
import json
import os
import smtplib
from email.mime.text import MIMEText

ADMIN_EMAIL = "nomenjanhr@gmail.com"
EMAIL_SENDER = "example@gmail.com"
EMAIL_PASSWORD = "**********"  # Use an app password, not your Gmail password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "secret-key-change-this"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    for u in users.values():
        if u["id"] == user_id:
            return User(u["id"], u["username"], u["role"], u.get("entity"))
    return None

DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

USERS_FILE = "users.json"

# Load users
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# Simple User class
class User(UserMixin):
    def __init__(self, id, username, role, entity=None):
        self.id = id
        self.username = username
        self.role = role
        self.entity = entity

    def get_role(self):
        return self.role

def send_admin_notification(license_type, price, validity, expiration_date, submitted_by):
    subject = "New License Submitted for Approval"
    body = f"""
    A new license has been submitted:

    - Type: {license_type}
    - Price: {price}
    - Validity: {validity}
    - Expiration Date: {expiration_date}
    - Submitted by: {submitted_by}

    Please log in to the admin panel to approve or reject it.
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ADMIN_EMAIL

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, ADMIN_EMAIL, msg.as_string())
        server.quit()
        print("Admin notified successfully.")
    except Exception as e:
        print("Failed to send email:", e)


@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/licenses", methods=["GET"])
def get_licenses():
    return jsonify(load_db())

@app.route("/license", methods=["POST"])
@login_required
def add_license():
    data = request.get_json()
    try:
        expiration = datetime.strptime(data["expiration_date"], "%Y-%m-%d").date()
        if expiration < datetime.now().date():
            return jsonify({"error": "Expiration date cannot be in the past"}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    license_entry = {
        "id": str(uuid.uuid4()),
        "license_type": data.get("license_type"),
        "price": data.get("price"),
        "validity": data.get("validity"),
        "expiration_date": data.get("expiration_date")
    }

    licenses = load_db()
    licenses.append(license_entry)
    save_db(licenses)
    submitted_by = session.get('username', 'Anonymous')
    
    # Existing code to extract form data
    """license_type = request.form['license_type']
    price = request.form['price']
    validity = request.form['validity']
    expiration_date = request.form['expiration']

    # Call email function
    send_admin_notification(license_type, price, validity, expiration_date, submitted_by)
    """
    return jsonify({"message": "License added", "license": license_entry}), 201
    

@app.route("/license/<license_id>", methods=["DELETE"])
def delete_license(license_id):
    licenses = load_db()
    updated = [l for l in licenses if l["id"] != license_id]
    if len(updated) == len(licenses):
        return jsonify({"error": "License not found"}), 404
    save_db(updated)
    return jsonify({"message": f"License {license_id} deleted"}), 200

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        data = request.form
        username = data.get("username")
        password = data.get("password")

        user_data = users.get(username)
        if user_data and user_data["password"] == password:
            user = User(user_data["id"], username, user_data["role"], user_data.get("entity"))
            login_user(user)
            return render_template("index.html")
        return "Invalid credentials", 401

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        entity = request.form.get("entity") if role == "CISO" else None

        users = load_users()
        if username in users:
            return "User already exists", 400

        user_id = str(len(users) + 1)
        users[username] = {
            "id": user_id,
            "username": username,
            "password": password,
            "role": role,
            "entity": entity
        }

        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)

        return redirect(url_for("login"))

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
