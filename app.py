from flask import Flask, request, jsonify, render_template
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message

from uuid import uuid4
import uuid
import json
import os


app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "secret-key-change-this"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Gmail configuration 

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = '16-digit code from gmail app code'
app.config['MAIL_DEFAULT_SENDER'] = ('License Manager', 'your-email@gmail.com')


mail = Mail(app)

def send_notification_email(subject, recipients, body):
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body
        )
        mail.send(msg)
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False

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
    
# Save Users
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# Simple User class
class User(UserMixin):
    def __init__(self, id, username, role, entity=None):
        self.id = id
        self.username = username
        self.role = role
        self.entity = entity

    def get_role(self):
        return self.role


@app.route("/")
@login_required
def home():
    user_info = {
        "username": current_user.username,
        "entity": current_user.entity
    }
    return render_template("index.html",user=user_info)

@app.route("/insertion")
def insertion():
    return render_template("insertion.html") 

@app.route("/licenses", methods=["GET"])
def get_licenses():
    return jsonify(load_db())

@app.route("/users")
def get_users():
    data = load_users()
    users = list(data.values())
    return jsonify({"users": users})

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
        "license_name": data.get("license_name"),
        "price": data.get("price"),
        "validity": data.get("validity"),
        "expiration_date": data.get("expiration_date"),
        "status": "Pending"
    }

    licenses = load_db()
    licenses.append(license_entry)
    save_db(licenses)
    submitted_by = session.get('username', 'Anonymous')
    
    body = f"""New license added:
Name: {data.get('license_name')}
Price: {data.get('price')}
Validity: {data.get('validity')}
Expiration Date: {data.get('expiration_date')}"""

    send_notification_email(
        subject="New License Added",
        recipients=["nomenjanhr@gmail.com"],
        body=body
    )
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
            if user_data["status"] == "pending":
                return "Your account is pending approval by an admin.", 403
            user = User(user_data["id"], username, user_data["role"], user_data.get("entity"))
            login_user(user)
            user_info = {
                "username": username,
                "entity": user_data.get("entity")
            }
            return render_template("index.html",user=user_info)
        return "Invalid credentials", 401

    return render_template("login.html")

"""
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_users()

        user = next((u for u in users if u["username"] == username and u["password"] == password), None)
        
        if not user:
            return "Invalid credentials", 401
        
        if user["status"] != "approved":
            return "Your account is pending approval by an admin.", 403

        login_user(User(**user))
        return redirect(url_for("index.html"))
    
    return render_template("login.html")
"""
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
            "entity": entity,
            "status": "pending"
        }

        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/admin/users")
@login_required
def admin_users():
    if current_user.role != "Admin":
        return "Unauthorized", 403

    users = load_users()
    return render_template("admin_users.html", users=users)

@app.route("/approve_user/<user_id>", methods=["POST"])
def approve_user(user_id):
    data = load_users()
    for user_key, user in data.items():
        if user.get("id") == user_id:
            user["status"] = "approved"
            save_users(data)
            return jsonify({"message": "User approved"})
    return jsonify({"error": "User not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
