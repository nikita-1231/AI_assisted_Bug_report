import pyodbc
from flask import Flask, request, jsonify, render_template
import re
from werkzeug.security import generate_password_hash

print("Starting app...")
app = Flask(__name__)

print("Connecting to database...")
conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=DESKTOP-66K8B9A\SQLEXPRESS;"
    r"DATABASE=SignupDB;"
    r"Trusted_Connection=yes;"
)

cursor = conn.cursor()
print("Database connected successfully")
@app.route('/')
def home():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    mobile = data.get('mobile')
    password = data.get('password')

    # ---- required fields ----
    if not username or not email or not mobile or not password:
        return jsonify({"error": "All fields are required"}), 400

    username = username.lower()
    email = email.lower()

    # ---- mobile validation ----
    if not re.fullmatch(r"[6-9]\d{9}", mobile):
        return jsonify({"error": "Invalid mobile number"}), 400

    # ---- password validation ----
    password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    if not re.fullmatch(password_pattern, password):
        return jsonify({
            "error": "Password must be 8 chars with upper, lower, number & special character"
        }), 400

    # ---- hash password ----
    password_hash = generate_password_hash(password)

    # ---- check username ----
    cursor.execute("SELECT 1 FROM SignUp  WHERE LOWER(username) = ?", (username,))
    if cursor.fetchone():
        return jsonify({"error": "Username already exists"}), 409

    # ---- check email ----
    cursor.execute("SELECT 1 FROM SignUp WHERE LOWER(email) = ?", (email,))
    if cursor.fetchone():
        return jsonify({"error": "Email already exists"}), 409

    # ---- check mobile ----
    cursor.execute("SELECT 1 FROM SignUp WHERE mobile = ?", (mobile,))
    if cursor.fetchone():
        return jsonify({"error": "Mobile number already exists"}), 409

    # ---- insert data ----
    cursor.execute(
        "INSERT INTO SignUp (username, email, mobile, password_hash) VALUES (?, ?, ?, ?)",
        (username, email, mobile, password_hash)
    )
    conn.commit()

    return jsonify({
        "message": "Signup successful",
        "username": username,
        "email": email,
        "mobile":mobile,
        
    }), 201


#  how to get data.......
@app.route('/signup', methods=['GET'])
def get_signup():
    cursor.execute(
        "SELECT id, username, email, mobile, password_hash,created_at FROM SignUp"
    )
    rows = cursor.fetchall()

    SignUp = []
    for row in rows:
        SignUp.append({
            "id": row.id,
            "username": row.username,
            "email": row.email,
            # "mobile": row.mobile,
             "password_hash": row.password_hash,
            
            "created_at": str(row.created_at)   
        })

    return jsonify(SignUp), 200
   # delete the user method....

@app.route("/signup/<int:_id>", methods=["DELETE"])
def delete_user(_id):
    try:
        # pehle check karo user exist karta hai ya nahi
        cursor.execute("SELECT * FROM SignUp WHERE id=?", (_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # delete query
        cursor.execute("DELETE FROM SignUp WHERE id=?", (_id,))
        conn.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        print("DELETE ERROR:", e)   # terminal me real error dikhega
        return jsonify({"error": "Internal server error"}), 500

   # Put method .......
@app.route("/signup/<int:_id>", methods=["PUT"])
def update_user(_id):
 try:
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    mobile = data.get("mobile")
    password=data.get("password")
    
    if not data:
            return jsonify({"error": "No data provided"}), 400
    
    cursor.execute("Select * from SignUp  WHERE id=?",(_id,))
    user = cursor.fetchone()
    if not user:
            return jsonify({"error": "User not found"}), 404

    fields = []
    values = []
# ---- username update ----
    if username:
            username = username.lower()

            # check duplicate username
            cursor.execute(
                "SELECT id FROM SignUp WHERE LOWER(username)=? AND id<>?",
                (username, _id)
            )
            if cursor.fetchone():
                return jsonify({"error": "Username already exists"}), 409

            fields.append("username=?")
            values.append(username)

        # ---- email update ----
    if email:
            email = email.lower()

            cursor.execute(
                "SELECT id FROM SignUp WHERE LOWER(email)=? AND id<>?",
                (email, _id)
            )
            if cursor.fetchone():
                return jsonify({"error": "Email already exists"}), 409

            fields.append("email=?")
            values.append(email)

        # ---- mobile update ----
    if mobile:
            if not re.fullmatch(r"[6-9]\d{9}", mobile):
                return jsonify({"error": "Invalid mobile number"}), 400

            cursor.execute(
                "SELECT id FROM SignUp WHERE mobile=? AND id<>?",
                (mobile, _id)
            )
            if cursor.fetchone():
                return jsonify({"error": "Mobile already exists"}), 409

            fields.append("mobile=?")
            values.append(mobile)

        # ---- password update ----
    if password:
            if len(password) < 8:
                return jsonify({"error": "Password too short"}), 400

            password_hash = generate_password_hash(password)
            fields.append("password_hash=?")
            values.append(password_hash)

    if not fields:
            return jsonify({"error": "Nothing to update"}), 400

    query = f"UPDATE SignUp SET {', '.join(fields)} WHERE id=?"
    values.append(_id)

    cursor.execute(query, tuple(values))
    conn.commit()
    
    if cursor.rowcount == 0:
       return jsonify({"message": "No changes made"}), 200
    return jsonify({"message": "User updated successfully"}), 200
 except Exception as e:
    print("UPDATE ERROR:", e)
    return jsonify({"error": "Internal server error"}), 500
   

# login module routing 
@app.route("/login")
def login_page():
    return render_template("login.html")

from werkzeug.security import check_password_hash

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    cursor.execute(
        "SELECT id, username, password_hash FROM SignUp WHERE LOWER(email)=?",
        (email.lower(),)
    )
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid password"}), 401

    return jsonify({
        "message": "Login successful",
        "username": user.username
    }), 200

   
    


if __name__ == "__main__": 
    print("Starting Flask server...") 
    app.run(debug=True)
