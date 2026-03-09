import re
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

# ---------------- MONGODB ----------------
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
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

# ---------------- SMART TEST CASE GENERATOR ----------------
def generate_test_cases(title, module, steps, expected, actual):

    return [
        {"id":"TC-01","desc":f"Verify {module} functionality","steps":steps,"expected":expected},
        {"id":"TC-02","desc":"Verify valid input handling","steps":steps,"expected":expected},
        {"id":"TC-03","desc":"Verify invalid input handling","steps":steps,"expected":"Error message should appear"},
        {"id":"TC-04","desc":"Verify system does not crash","steps":steps,"expected":"System should remain stable"},
        {"id":"TC-05","desc":"Verify error logging","steps":steps,"expected":"Error should be logged"},
        {"id":"TC-06","desc":"Verify UI response","steps":steps,"expected":"Proper UI feedback"},
        {"id":"TC-07","desc":"Verify backend validation","steps":steps,"expected":"Validation should trigger"},
        {"id":"TC-08","desc":"Verify database response","steps":steps,"expected":"Correct DB operation"},
        {"id":"TC-09","desc":"Verify after bug fix","steps":steps,"expected":expected},
        {"id":"TC-10","desc":"Regression test for module","steps":steps,"expected":expected}
    ]

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("signup.html")

# ---------------- BUG REPORT PAGE ----------------
@app.route("/bug_report")
def bug_report_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("bug_report.html")

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
        "bug_id":bug_id,
        "title":title,
        "module":module,
        "steps":steps,
        "expected":expected,
        "actual":actual,
        "severity":severity,
        "priority":priority,
        "status":"Open",
        "reported_by":session["user_id"],
        "created_at":datetime.utcnow()
    })

    test_cases = generate_test_cases(title,module,steps,expected,actual)

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

    c = canvas.Canvas(file_path,pagesize=letter)

    c.drawString(100,750,"Bug Test Case Report")
    c.drawString(100,720,f"Title: {title}")
    c.drawString(100,700,f"Module: {module}")

    c.save()

    return send_file(file_path,as_attachment=True)

# ---------------- DELETE BUG ----------------
@app.route("/delete_bug/<bug_id>", methods=["POST"])
def delete_bug(bug_id):

    bug_col.delete_one({"_id":ObjectId(bug_id)})

    return jsonify({"message":"Bug deleted"})

if __name__ == "__main__":
     app.run(debug=True)