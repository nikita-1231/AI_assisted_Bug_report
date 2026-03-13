import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson import ObjectId
from spellchecker import SpellChecker

# PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

print("App is starting...")

# ---------------- MONGODB ----------------


MONGO_URI = "mongodb://localhost:27017/"

if not MONGO_URI:
    raise Exception("MONGO_URI not set")

client = MongoClient(MONGO_URI)

try:
    client.admin.command("ping")
    print("Mongo connected")
except Exception as e:
    print("Mongo connection error:", e)

db = client.blogs

signup_col = db.signup
bug_col = db.bug_report

spell = SpellChecker()

# ---------------- TEXT CLEAN ----------------

def clean_text(text):
    if not text:
        return ""
    return " ".join(
        spell.correction(word) if word.isalpha() else word
        for word in text.split()
    )

# ---------------- BUG ID GENERATOR ----------------

def generate_bug_id():

    last_bug = bug_col.find_one(sort=[("created_at", -1)])

    if not last_bug or "bug_id" not in last_bug:
        return "BUG-001"

    last_id = int(last_bug["bug_id"].split("-")[1])
    new_id = last_id + 1

    return f"BUG-{new_id:03d}"

# ---------------- TEST CASE GENERATOR ----------------

def generate_test_cases(title, module, steps, expected, actual):

    return [
        {"id":"TC-01","desc":f"Verify {module} functionality","steps":steps,"expected":expected},
        {"id":"TC-02","desc":"Verify valid input handling","steps":steps,"expected":expected},
        {"id":"TC-03","desc":"Verify invalid input handling","steps":steps,"expected":"Error message should appear"},
        {"id":"TC-04","desc":"Verify system stability","steps":steps,"expected":"System should not crash"},
        {"id":"TC-05","desc":"Verify error logging","steps":steps,"expected":"Error must be logged"},
        {"id":"TC-06","desc":"Verify UI response","steps":steps,"expected":"Proper UI feedback"},
        {"id":"TC-07","desc":"Verify backend validation","steps":steps,"expected":"Validation should trigger"},
        {"id":"TC-08","desc":"Verify database operation","steps":steps,"expected":"Data should be saved correctly"},
        {"id":"TC-09","desc":"Verify bug after fix","steps":steps,"expected":expected},
        {"id":"TC-10","desc":"Regression test","steps":steps,"expected":expected}
    ]

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("signup.html")

# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["POST"])
def signup():

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    if signup_col.find_one({"email": email}):
        return "User already exists"

    hashed_password = generate_password_hash(password)

    signup_col.insert_one({
        "name": name,
        "email": email,
        "password": hashed_password
    })

    return redirect("/login")

# ---------------- LOGIN PAGE ----------------

@app.route("/login")
def login_page():
    return render_template("login.html")

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = signup_col.find_one({"email": email})

        if user and user["password"] == password:

            session["user_id"] = str(user["_id"])   # IMPORTANT

            return redirect("/bug_report")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html", username=session["user_name"])

# ---------------- VIEW BUG REPORTS ----------------

@app.route("/viewdetails")
def viewdetails():

    if "user_id" not in session:
        return redirect("/login")

    reports = list(bug_col.find({"reported_by": session["user_id"]}))

    for r in reports:
        r["_id"] = str(r["_id"])

    return render_template("viewdetails.html", reports=reports)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    return redirect("/login")

# ---------------- BUG REPORT PAGE ----------------

@app.route("/bug_report")
def bug_report_page():

    if "user_id" not in session:
        return redirect("/login")

    bugs = list(bug_col.find({"reported_by": session["user_id"]}))

    # Convert ObjectId to string
    for bug in bugs:
        bug["_id"] = str(bug["_id"])

    return render_template("bug_report.html", bugs=bugs)

# ---------------- GENERATE BUG ----------------

@app.route("/generate-bug", methods=["POST"])
def generate_bug():

    if "user_id" not in session:
        return redirect("/login")

    title = clean_text(request.form.get("title"))
    module = clean_text(request.form.get("module"))
    steps = clean_text(request.form.get("steps"))
    expected = clean_text(request.form.get("expected"))
    actual = clean_text(request.form.get("actual"))

    severity = priority = "Low"

    if "error" in actual.lower() or "crash" in actual.lower():
        severity = priority = "High"
    elif "not working" in actual.lower():
        severity = priority = "Medium"

    bug_id = generate_bug_id()

    bug_col.insert_one({
        "bug_id": bug_id,
        "title": title,
        "module": module,
        "steps": steps,
        "expected": expected,
        "actual": actual,
        "severity": severity,
        "priority": priority,
        "status": "Open",
        "reported_by": session["user_id"],
        "created_at": datetime.utcnow()
    })

    test_cases = generate_test_cases(title, module, steps, expected, actual)

    return render_template(
        "testcase.html",
        bug_id=bug_id,
        title=title,
        module=module,
        steps=steps,
        expected=expected,
        actual=actual,
        severity=severity,
        priority=priority,
        test_cases=test_cases
    )

# ---------------- EXPORT PDF ----------------

@app.route("/export_pdf")
def export_pdf():

    title = request.args.get("title")
    module = request.args.get("module")

    file_path = "testcases.pdf"

    c = canvas.Canvas(file_path, pagesize=letter)

    c.drawString(100,750,"Bug Test Case Report")
    c.drawString(100,720,f"Title: {title}")
    c.drawString(100,700,f"Module: {module}")

    c.save()

    return send_file(file_path, as_attachment=True)

# ---------------- DELETE BUG ----------------

@app.route("/delete_bug/<bug_id>", methods=["POST"])
def delete_bug(bug_id):

    bug_col.delete_one({"_id": ObjectId(bug_id)})

    return jsonify({"message": "Bug deleted"})

# ---------------- UPDATE BUG ----------------

@app.route("/update_bug/<id>", methods=["POST"])
def update_bug(id):

    data = request.get_json()

    bug_col.update_one(
        {"_id": ObjectId(id)},
        {"$set":{
            "title": data["title"],
            "module": data["module"],
            "steps": data["steps"],
            "expected": data["expected"],
            "actual": data["actual"]
        }}
    )

    return jsonify({"message":"Bug updated successfully"})

# ---------------- UPDATE STATUS ----------------

@app.route("/update_status/<id>", methods=["POST"])
def update_status(id):

    data = request.get_json()

    bug_col.update_one(
        {"_id": ObjectId(id)},
        {"$set":{"status": data["status"]}}
    )

    return jsonify({"message":"Status updated"})

# ---------------- TEST ROUTE ----------------

@app.route("/test")
def test():
    return "Server is running"


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)