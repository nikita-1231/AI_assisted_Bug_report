import re
import os
from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from pymongo import MongoClient
from spellchecker import SpellChecker

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

print("Starting app...")

# ---------------- MONGODB CONNECTION ----------------
print("Connecting to MongoDB...")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client.blogs
signup_col = db.signup
bug_col = db.bugreport

print("MongoDB connected successfully")

# ---------------- SPELL ----------------
spell = SpellChecker()

def clean_text(text):
    if not text:
        return ""
    words = text.split()
    return " ".join(
        spell.correction(word) if word.isalpha() else word
        for word in words
    )

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("signup.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()

        username = data.get("username", "").lower()
        email = data.get("email", "").lower()
        mobile = data.get("mobile")
        password = data.get("password")

        if not all([username, email, mobile, password]):
            return jsonify({"error": "All fields are required"}), 400

        if not re.fullmatch(r"[6-9]\d{9}", mobile):
            return jsonify({"error": "Invalid mobile number"}), 400

        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        if not re.fullmatch(password_pattern, password):
            return jsonify({"error": "Weak password"}), 400

        if signup_col.find_one({"email": email}):
            return jsonify({"error": "Email already exists"}), 409

        if signup_col.find_one({"name": username}):
            return jsonify({"error": "Username already exists"}), 409

        signup_col.insert_one({
            "name": username,
            "email": email,
            "mobile": mobile,
            "password": generate_password_hash(password),
            "created_at": datetime.utcnow()
        })

        return jsonify({"message": "Signup successful"}), 201

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({"error": "Signup failed"}), 500

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email", "").lower()
        password = data.get("password")

        user = signup_col.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid credentials"}), 401

        session["user_id"] = str(user["_id"])
        session["username"] = user["name"]

        return jsonify({"message": "Login successful"}), 200

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"error": "Login failed"}), 500

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html", username=session["username"])

# ---------------- BUG REPORT ----------------
@app.route("/bug_report")
def bug_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("bug_report.html")

@app.route("/generate-bug", methods=["POST"])
def generate_bug():
    title = clean_text(request.form.get("title"))
    module = clean_text(request.form.get("module"))
    steps = clean_text(request.form.get("steps"))
    expected = clean_text(request.form.get("expected"))
    actual = clean_text(request.form.get("actual"))

    severity = priority = "Low"
    if actual and ("crash" in actual.lower() or "error" in actual.lower()):
        severity = priority = "High"
    elif actual and "not working" in actual.lower():
        severity = priority = "Medium"

    bug_col.insert_one({
        "title": title,
        "module": module,
        "steps": steps,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "priority": priority,
        "reported_by": session["user_id"],
        "created_at": datetime.utcnow()
    })

    return render_template("testcase.html", **locals())

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- GLOBAL ERROR ----------------
@app.errorhandler(Exception)
def handle_exception(e):
    print("ERROR:", e)
    return jsonify({"error": "Internal Server Error"}), 500