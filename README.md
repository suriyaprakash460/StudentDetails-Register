# 🎓 Student Details Register System

[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-success?style=flat-square)](https://github.com/suriyaprakash460/StudentDetails-Register)
[![Technology Stack](https://img.shields.io/badge/Stack-Flask%20%7C%20MySQL%20%7C%20Bootstrap-blue?style=flat-square)](https://flask.palletsprojects.com/)

A premium, production-ready Full Stack Web Application designed for efficient management of student records. Featuring a state-of-the-art **All-India Geography Integration**, real-time AJAX search, and a secure session-based authentication system.

---

## 🌟 Key Features

### 📍 Intelligent Address System (Advanced Integration)
- **All-India Geodata**: Integrated cascading selects for **State → District → Taluka → Village**.
- **PINCODE Power-Search**: Input any 6-digit Indian PIN and click "Fetch" to automatically populate the State, District, and Taluka via the Postal Pincode API.
- **Village Autocomplete**: Real-time suggestions for Village/Post-Office names.

### 🔍 Real-Time Interaction
- **AJAX Live Search**: Filter thousands of students instantly by Name, Course, or Address without refreshing the page.
- **Server-Side Rendering**: Fast initial loads with optimized Jinja2 templates.
- **Dynamic Date Fields**: Re-designed horizontal **Date-Month-Year** selectors with extended support up to the year **3050**.

### 🔐 Security & Reliability
- **Secure Authentication**: Password hashing using **Werkzeug's PBKDF2** (No plain-text storage).
- **Auto Session Timeout**: Configurable window (30 min) with an interactive **Modal Warning** and countdown timer to prevent unauthorized access.
- **SQL Injection Protection**: Fully parameterized queries for all Database interactions.
- **Gap-Free ID Management**: Automatic ID reordering systems to ensure a sequential, gap-free registry.

### 📱 Premium UX/UI
- **Responsive Design**: Built with **Bootstrap 5**, providing a seamless experience across Mobile, Tablet, and Desktop.
- **Micro-Animations**: Smooth transitions, hover effects, and loading spinners for a professional feel.
- **Modern Typography**: Utilizing the **Inter** font family for maximum readability.

---

## 🛠️ Technology Stack

| Component | Technology Used |
| :--- | :--- |
| **Backend** | Python 3, Flask |
| **Database** | MySQL |
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript (ES6+) |
| **Styling** | Bootstrap 5, Bootstrap Icons |
| **Auth** | Flask Session, Werkzeug Security |
| **API** | Data.gov.in / Postal Pincode API |

---

## 🚀 Quick Start

### 1. Database Setup
Ensure you have MySQL installed and a database named `student_db` created. Run these queries to initialize tables:

```sql
CREATE DATABASE student_db;
USE student_db;

-- Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Students Table
CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    dob DATE NOT NULL,
    course VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    admission_date DATE NOT NULL
);
```

### 2. Configuration
Update the database credentials in `main.py`:

```python
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD",
        database="student_db"
    )
```

### 3. Run the App
```bash
pip install flask mysql-connector-python werkzeug
python main.py
```
Visit `http://127.0.0.1:5000` to start managing records!

---

## 📂 Project Structure
- `main.py`: Flask application core with Auth & CRUD logic.
- `static/`: Contains JS, CSS, and `india_geodata.json` for address lookups.
- `templates/`: Professional Jinja2 templates (Base, Add, Edit, View, Auth).
- `README.md`: Modern documentation for the project.

---

## 📝 License
Built for educational and administrative excellence.  
&copy; 2024 **StudentMS** &mdash; Developed by [Suriyaprakash S](https://github.com/suriyaprakash460)
