import re
from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from pymongo import MongoClient
from bson import ObjectId

from spellchecker import SpellChecker
import language_tool_python

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = "super_secret_key_123"

print("Starting app...")

# ---------------- MONGODB CONNECTION ----------------
print("Connecting to MongoDB...")

MONGO_URI = "mongodb+srv://admin:VDlXl8oHgIOHBEix@cluster0.h8ttfq3.mongodb.net/blogs?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

db = client.blogs
signup_col = db.signup
bug_col = db.bugreport

print("MongoDB connected successfully")

# ---------------- SPELL & GRAMMAR ----------------
spell = SpellChecker()
tool = language_tool_python.LanguageTool('en-US')

def clean_text(text):
    words = text.split()
    corrected_words = []

    for word in words:
        if word.isalpha():
            corrected_words.append(spell.correction(word))
        else:
            corrected_words.append(word)

    corrected_text = " ".join(corrected_words)
    matches = tool.check(corrected_text)
    final_text = language_tool_python.utils.correct(corrected_text, matches)
    return final_text

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("signup.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    username = data.get("username", "").lower()
    email = data.get("email", "").lower()
    mobile = data.get("mobile")
    password = data.get("password")

    if not username or not email or not mobile or not password:
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

    password_hash = generate_password_hash(password)

    signup_col.insert_one({
        "name": username,
        "email": email,
        "mobile": mobile,
        "password": password_hash,
        "created_at": datetime.utcnow()
    })

    return jsonify({"message": "Signup successful"}), 201

# ---------------- GET USERS ----------------
@app.route("/signup", methods=["GET"])
def get_users():
    users = signup_col.find({}, {"password": 0})
    return jsonify(list(users)), 200

# ---------------- UPDATE USER ----------------
@app.route("/signup/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    update_data = {}

    if "username" in data:
        update_data["name"] = data["username"].lower()
    if "email" in data:
        update_data["email"] = data["email"].lower()
    if "mobile" in data:
        update_data["mobile"] = data["mobile"]
    if "password" in data:
        update_data["password"] = generate_password_hash(data["password"])

    if not update_data:
        return jsonify({"error": "Nothing to update"}), 400

    result = signup_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User updated successfully"}), 200

# ---------------- DELETE USER ----------------
@app.route("/signup/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    result = signup_col.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": "User deleted successfully"}), 200

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").lower()
    password = data.get("password")

    user = signup_col.find_one({"email": email})

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid password"}), 401

    session["user_id"] = str(user["_id"])
    session["username"] = user["name"]

    return jsonify({"message": "Login successful", "redirect": "/dashboard"}), 200

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html", username=session["username"])

# ---------------- BUG REPORT PAGE ----------------
@app.route("/bug_report")
def bug_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("bug_report.html")

# ---------------- GENERATE BUG ----------------
@app.route("/generate-bug", methods=["POST"])
def generate_bug():
    title = clean_text(request.form.get("title"))
    module = clean_text(request.form.get("module"))
    steps = clean_text(request.form.get("steps"))
    expected = clean_text(request.form.get("expected"))
    actual = clean_text(request.form.get("actual"))

    severity = "Low"
    priority = "Low"

    if "crash" in actual.lower() or "error" in actual.lower():
        severity = priority = "High"
    elif "not working" in actual.lower():
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

    return render_template(
        "testcase.html",
        title=title,
        module=module,
        steps=steps,
        expected=expected,
        actual=actual,
        severity=severity,
        priority=priority
    )

# ---------------- VIEW BUG REPORTS ----------------
@app.route("/viewdetails")
def view_reports():
    if "user_id" not in session:
        return redirect("/login")

    reports = bug_col.find().sort("created_at", -1)
    return render_template("viewdetails.html", reports=reports)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------

if __name__ == "__main__":
 app.run(host="0.0.0.0", port=5000)