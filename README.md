# Project Demo

# AI Assisted Bug Reporting and testcases

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-brightgreen)
![Deployment](https://img.shields.io/badge/Deployment-Railway-purple)
![Status](https://img.shields.io/badge/Project-Active-success)

---

# Project Overview

The AI Assisted Bug Report System** is a full-stack web application that allows users to report, manage, and track software bugs efficiently.

The system includes a rule-based AI logic that automatically suggests:

* Bug **Severity**
* Bug **Priority**
* Suggested **Test Cases**

This helps developers categorize and resolve bugs faster.

---

# Live Demo link

```
aiassistedbugreport-production.up.railway.app
```


---

# Tech Stack

## Backend

* Python
* Flask
* Gunicorn

## Database

* MongoDB Atlas

## Frontend

* HTML
* CSS
* JavaScript

## Deployment

* Railway

---

# Project Architecture


User
  │
  ▼
Frontend (HTML / CSS / JS)
  │
  ▼
Flask Backend (app.py)
  │
  ▼
AI Rule Logic
  │
  ▼
MongoDB Database


---

# Project Structure


AI_assisted_Bug_report/
│
├── app.py
├── requirements.txt
├── Procfile
├── README.md
│
├── templates/
│   ├── signup.html
│   ├── login.html
│   ├── bug_report.html
│   └── viewdetails.html
│
├── static/
│   └── css/
│       ├── style.css
│       └── viewdetails.css


---

# Features

## Authentication System

* User Signup
* User Login
* Secure password hashing

---

## Bug Reporting

Users can report bugs with:

* Title
* Module
* Steps to reproduce
* Expected result
* Actual result

---

## AI Bug Analysis

The system automatically generates:

* Severity level
* Priority level
* Suggested test cases

This is implemented using rule-based AI logic.

---

## Bug Management

Users can:

* View bug reports
* Update bug details
* Delete bug reports
* Change bug status

Status types:

* Open
* In Progress
* Fixed

---

## Dynamic UI Features

Using JavaScript:

* Update bug status instantly
* Delete bugs without page reload
* Edit bug reports through modal popup

---

# Database Design

## Users Collection

```
{
  username: String,
  email: String,
  phone no.:string,
  password: String
}
```

---

## Bugs Collection

```
{
  title: String,
  module: String,
  steps: String,
  expected: String,
  actual: String,
  severity: String,
  priority: String,
  status: String,
  created_at: Date
}
```

---

# Environment Variables

The following environment variables are required for deployment:

```
MONGO_URI = MongoDB connection string
SECRET_KEY = Flask secret key
ENV = production
```

---

# Installation (Run Locally)

## Clone Repository

```
git clone https://github.com/yourusername/AI_assisted_Bug_report.git
cd AI_assisted_Bug_report
```

---

## Install Dependencies

```
pip install -r requirements.txt
```

---

## Run the App

```
python app.py or py app.py
```

Open browser:

```
http://127.0.0.1:5000
```

---

# Screenshots

### Signup Page

(Add screenshot here)

### Login Page

(Add screenshot here)

### Bug Dashboard

(Add screenshot here)

---

# Future Improvements

Planned features for the next versions:

### AI Improvements

* NLP based bug classification
* Machine learning severity prediction
* Duplicate bug detection

### Feature Enhancements

* Screenshot upload with bug report
* Admin dashboard
* Bug search and filtering
* Pagination

### Security

* JWT authentication
* Rate limiting
* Input validation improvements

---

# Learning Outcomes

This project demonstrates:

* Full-stack web development
* RESTful backend design
* Authentication system
* MongoDB database integration
* Cloud deployment
* Basic AI rule-based automation

---

# Author

Nikita Kumari
MCA Student
Aspiring Software Developer

---

# License

This project is for educational and portfolio purposes.
