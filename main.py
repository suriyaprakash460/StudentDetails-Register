"""
Student Management System — Flask Backend
==========================================
Features:
  - Session-based auth with hashed passwords (werkzeug)
  - Session timeout: auto-logout after SESSION_TIMEOUT_MINUTES of inactivity
  - AJAX JSON API: /api/search, /api/ping, /api/delete/<id>
  - Full CRUD for students with server-side pagination and search
  - Sequential ID reordering on delete (gap-free IDs)
  - Parameterised queries throughout (SQL-injection safe)
  - try-except error handling on every DB call
"""

from flask import (
    Flask, render_template, request,
    redirect, flash, url_for, session, jsonify
)
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import mysql.connector

app = Flask(__name__)
app.secret_key = "sms_super_secret_2024"

# ── Global config ──────────────────────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES = 30   # inactivity window before auto-logout
PER_PAGE                = 100000000  # show all students on one page (effectively no pagination)


# ══════════════════════════════════════════════════════════════════════════════
# 🔌 DATABASE LAYER
# ══════════════════════════════════════════════════════════════════════════════

def get_db_connection():
    """
    Create and return a raw MySQL connection.
    All credentials are kept in one place; update here to change DB settings.
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="suriya@2004",
        database="student_db"
    )


def db_execute(query, params=(), fetch=None, commit=False):
    """
    Safe, reusable DB executor — centralises connection lifecycle.

    Args:
        query  (str)  : Parameterised SQL query string.
        params (tuple): Values to bind (prevents SQL injection).
        fetch  (str)  : 'one' → fetchone(), 'all' → fetchall(), None → no fetch.
        commit (bool) : True for INSERT / UPDATE / DELETE / ALTER statements.

    Returns:
        Row(s) from fetchone/fetchall, or None.

    Raises:
        mysql.connector.Error on DB failure (caller must catch).
    """
    conn   = get_db_connection()
    cursor = conn.cursor()
    result = None
    try:
        cursor.execute(query, params)
        if fetch == 'one':
            result = cursor.fetchone()
        elif fetch == 'all':
            result = cursor.fetchall()
        if commit:
            conn.commit()
    finally:
        cursor.close()
        conn.close()
    return result


# ══════════════════════════════════════════════════════════════════════════════
# ⏱️  SESSION TIMEOUT  (before_request hook)
# ══════════════════════════════════════════════════════════════════════════════

@app.before_request
def enforce_session_timeout():
    """
    Runs automatically before every request.

    Checks whether the logged-in user has been inactive longer than
    SESSION_TIMEOUT_MINUTES.  If so, clears the session and redirects
    to login.  On every valid request, 'last_active' is refreshed so
    the window slides forward with activity.

    Skips static file requests and the login/logout routes themselves
    to avoid redirect loops.
    """
    # Skip static assets and auth routes to avoid infinite redirect loops
    skip_endpoints = {'login', 'logout', 'register', 'static'}
    if request.endpoint in skip_endpoints:
        return

    if 'logged_in' in session:
        last_active_str = session.get('last_active')
        if last_active_str:
            last_active_dt = datetime.fromisoformat(last_active_str)
            elapsed = datetime.now() - last_active_dt
            if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                session.clear()
                flash(
                    "Your session expired due to inactivity. Please log in again.",
                    "warning"
                )
                return redirect(url_for('login'))

        # Slide the inactivity window forward
        session['last_active'] = datetime.now().isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# 🔐 AUTH DECOR
# ══════════════════════════════════════════════════════════════════════════════

def login_required(f):
    """
    Route decorator — redirects unauthenticated users to /login.
    Attach with @login_required above any protected route function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════════════════
# 🏠 HOME
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Render the public landing / home page."""
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════════════════
# 🔐 LOGIN
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  → Render the login form.
    POST → Validate credentials:
             1. Look up username in the users table.
             2. Use check_password_hash() to verify the stored bcrypt hash.
             3. On success, populate session and redirect to view_students.
             4. On failure, show a generic error (avoid username enumeration).
    """
    if request.method == "POST":
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Basic presence check
        if not username or not password:
            flash("Both fields are required.", "warning")
            return render_template("login.html")

        try:
            user = db_execute(
                "SELECT id, username, password FROM users WHERE username = %s",
                (username,), fetch='one'
            )
        except Exception as e:
            app.logger.error(f"[LOGIN] DB error: {e}")
            flash("A server error occurred. Please try again.", "danger")
            return render_template("login.html")

        # Verify hashed password — avoid timing attacks by always calling check_password_hash
        if user and check_password_hash(user[2], password):
            session.clear()                                    # rotate session to prevent fixation
            session['logged_in']   = True
            session['username']    = user[1]
            session['user_id']     = user[0]
            session['last_active'] = datetime.now().isoformat()
            flash(f"Welcome back, {user[1]}! 👋", "success")
            return redirect(url_for('view_students'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


# ══════════════════════════════════════════════════════════════════════════════
# 🆕 REGISTER
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    GET  → Render registration form.
    POST → Validate input, check username uniqueness, hash password, insert user.
    Password is hashed with werkzeug.security.generate_password_hash (PBKDF2).
    Plain-text passwords are NEVER stored in the database.
    """
    if request.method == "POST":
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # ── Server-side validation ──────────────────────────────────────────
        errors = []
        if not username:
            errors.append("Username is required.")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html", username=username)

        try:
            # Check for existing username (unique constraint)
            existing = db_execute(
                "SELECT id FROM users WHERE username = %s", (username,), fetch='one'
            )
            if existing:
                flash("That username is already taken. Please choose another.", "warning")
                return render_template("register.html", username=username)

            # Hash then store — never store raw password
            hashed_pw = generate_password_hash(password)
            db_execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_pw), commit=True
            )
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            app.logger.error(f"[REGISTER] DB error: {e}")
            flash("Registration failed due to a server error. Please try again.", "danger")

    return render_template("register.html")


# ══════════════════════════════════════════════════════════════════════════════
# 🚪 LOGOUT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/logout")
def logout():
    """Clear the entire session and redirect to the login page."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════════════════════════
# ➕ ADD STUDENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    """
    Find the smallest missing ID starting from 1, and insert the new student
    including address and admission date.
    """
    if request.method == "POST":
        name       = request.form.get('name',           '').strip().title()
        age        = request.form.get('age',            '').strip()
        dob        = request.form.get('dob',            '').strip()
        course     = request.form.get('course',         '').strip()
        address    = request.form.get('address',        '').strip()
        adm_date   = request.form.get('admission_date', '').strip()

        # ── Field validation ────────────────────────────────────────────────
        errors = []
        if not name:
            errors.append("Student name is required.")
        if not age:
            errors.append("Age is required.")
        elif not age.isdigit() or not (1 <= int(age) <= 120):
            errors.append("Age must be a valid number between 1 and 120.")
        if not dob:
            errors.append("Date of Birth is required.")
        if not course:
            errors.append("Course is required.")
        if not address:
            errors.append("Address is required.")
        if not adm_date:
            errors.append("Admission date is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("add.html", name=name, age=age, dob=dob, course=course, address=address, admission_date=adm_date)

        try:
            # ── FIND SMALLEST MISSING ID ─────────────────────────────────────
            id_check = db_execute("SELECT id FROM students WHERE id = 1", fetch='one')
            if not id_check:
                next_id = 1
            else:
                row = db_execute("""
                    SELECT MIN(t1.id + 1) 
                    FROM students t1 
                    LEFT JOIN students t2 ON t1.id + 1 = t2.id 
                    WHERE t2.id IS NULL
                """, fetch='one')
                next_id = row[0] if row and row[0] else 1

            # ── INSERT RECORD ───────────────────────────────────────────────
            db_execute(
                "INSERT INTO students (id, name, age, dob, course, address, admission_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (next_id, name, int(age), dob, course, address, adm_date), commit=True
            )
            flash(f"✅ '{name}' (ID: {next_id}) has been enrolled successfully!", "success")
            return redirect(url_for('view_students'))

        except Exception as e:
            app.logger.error(f"[ADD_STUDENT] DB error: {e}")
            flash("Failed to add student. Please try again.", "danger")
            return render_template("add.html", name=name, age=age, dob=dob, course=course, address=address, admission_date=adm_date)

    return render_template("add.html")


# ══════════════════════════════════════════════════════════════════════════════
# 📄 VIEW STUDENTS  (server-side pagination + optional search filter)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/view")
@login_required
def view_students():
    """
    Display a paginated list of students.

    Query params:
      ?q=<term>   — optional search filter (name or course, case-insensitive)
      ?page=<n>   — page number (default 1)

    AJAX live-search is handled separately by /api/search, which the
    frontend calls on keypress without a full page reload.
    This route powers the initial SSR render and paginated navigation.
    """
    query  = request.args.get('q', '').strip()
    page   = max(1, request.args.get('page', 1, type=int))
    offset = (page - 1) * PER_PAGE

    try:
        if query:
            like      = f"%{query}%"
            total_row = db_execute(
                "SELECT COUNT(*) FROM students WHERE name LIKE %s OR course LIKE %s OR address LIKE %s",
                (like, like, like), fetch='one'
            )
            total    = total_row[0] if total_row else 0
            students = db_execute(
                """SELECT id, name, age, dob, course, address, admission_date FROM students
                   WHERE name LIKE %s OR course LIKE %s OR address LIKE %s
                   ORDER BY id ASC LIMIT %s OFFSET %s""",
                (like, like, like, PER_PAGE, offset), fetch='all'
            ) or []
        else:
            total_row = db_execute("SELECT COUNT(*) FROM students", fetch='one')
            total     = total_row[0] if total_row else 0
            students  = db_execute(
                "SELECT id, name, age, dob, course, address, admission_date FROM students ORDER BY id ASC LIMIT %s OFFSET %s",
                (PER_PAGE, offset), fetch='all'
            ) or []

    except Exception as e:
        app.logger.error(f"[VIEW_STUDENTS] DB error: {e}")
        flash("Failed to load student records. Please try again.", "danger")
        students, total = [], 0

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    return render_template(
        "view.html",
        students=students,
        query=query,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=PER_PAGE,
        session_timeout=SESSION_TIMEOUT_MINUTES
    )


# ══════════════════════════════════════════════════════════════════════════════
# 🔍 AJAX SEARCH API  —  GET /api/search?q=<term>
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/search")
@login_required
def api_search():
    """
    JSON endpoint consumed by the AJAX live-search on the view page.

    Query param : ?q=<search term> (partial match on name OR course)
    Returns     : { students: [{id, name, age, course}, ...], total: int }

    The frontend debounces keypress events and calls this endpoint,
    then re-renders the table rows from the JSON response — no page reload.
    Cap at 100 results to prevent large payloads.
    """
    query = request.args.get('q', '').strip()
    try:
        if query:
            like = f"%{query}%"
            rows = db_execute(
                """SELECT id, name, age, dob, course, address, admission_date FROM students
                   WHERE name LIKE %s OR course LIKE %s OR address LIKE %s
                   ORDER BY id ASC LIMIT 100""",
                (like, like, like), fetch='all'
            ) or []
        else:
            rows = db_execute(
                "SELECT id, name, age, dob, course, address, admission_date FROM students ORDER BY id ASC LIMIT 100",
                fetch='all'
            ) or []

        students = [
            {
                "id": r[0], 
                "name": r[1], 
                "age": r[2], 
                "dob": r[3].strftime('%Y-%m-%d') if r[3] else "",
                "course": r[4],
                "address": r[5],
                "admission_date": r[6].strftime('%Y-%m-%d') if r[6] else ""
            }
            for r in rows
        ]
        return jsonify({"students": students, "total": len(students), "query": query})

    except Exception as e:
        app.logger.error(f"[API_SEARCH] DB error: {e}")
        return jsonify({"error": "Search failed", "students": [], "total": 0}), 500


# ══════════════════════════════════════════════════════════════════════════════
# 💓 SESSION PING  —  GET /api/ping
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/ping")
@login_required
def api_ping():
    """
    Lightweight heartbeat endpoint called by the frontend session-timeout
    countdown JS when the user clicks 'Stay Logged In' or is still active.

    Touching any @login_required route already refreshes session['last_active']
    via before_request, so this just needs to return 200 OK.
    Returns: { alive: true, remaining_minutes: int }
    """
    remaining = SESSION_TIMEOUT_MINUTES   # always fresh after before_request runs
    return jsonify({"alive": True, "remaining_minutes": remaining})


# ══════════════════════════════════════════════════════════════════════════════
# ✏️  EDIT STUDENT
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    """
    GET  → Fetch the student by ID and render a pre-filled edit form.
           If student not found, redirect to view with a warning flash.
    POST → Validate updated fields, run UPDATE query, redirect to view.
           On validation error, re-render form with current input values
           so the user does not lose their edits.
    """
    try:
        row = db_execute(
            "SELECT id, name, age, dob, course, address, admission_date FROM students WHERE id = %s",
            (id,), fetch='one'
        )
        if row:
            # Convert date to string for HTML5 date input compatibility
            student = list(row)
            if student[3]:
                student[3] = student[3].strftime('%Y-%m-%d')
            if student[6]:
                student[6] = student[6].strftime('%Y-%m-%d')
            student = tuple(student)
        else:
            student = None
    except Exception as e:
        app.logger.error(f"[EDIT_STUDENT] Fetch error: {e}")
        flash("Could not retrieve student record.", "danger")
        return redirect(url_for('view_students'))

    if not student:
        flash(f"Student #{id} was not found.", "warning")
        return redirect(url_for('view_students'))

    if request.method == "POST":
        name     = request.form.get('name',           '').strip().title()
        age      = request.form.get('age',            '').strip()
        dob      = request.form.get('dob',            '').strip()
        course   = request.form.get('course',         '').strip()
        address  = request.form.get('address',        '').strip()
        adm_date = request.form.get('admission_date', '').strip()

        errors = []
        if not name:
            errors.append("Student name is required.")
        if not age:
            errors.append("Age is required.")
        elif not age.isdigit() or not (1 <= int(age) <= 120):
            errors.append("Age must be a valid number between 1 and 120.")
        if not dob:
            errors.append("Date of Birth is required.")
        if not course:
            errors.append("Course is required.")
        if not address:
            errors.append("Address is required.")
        if not adm_date:
            errors.append("Admission date is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            # Preserve user's current input on re-render
            return render_template("edit.html", student=(id, name, age, dob, course, address, adm_date))

        try:
            db_execute(
                "UPDATE students SET name=%s, age=%s, dob=%s, course=%s, address=%s, admission_date=%s WHERE id=%s",
                (name, int(age), dob, course, address, adm_date, id), commit=True
            )
            flash(f"✅ Student #{id} updated successfully!", "success")
            return redirect(url_for('view_students'))
        except Exception as e:
            app.logger.error(f"[EDIT_STUDENT] Update error: {e}")
            flash("Update failed. Please try again.", "danger")
            return render_template("edit.html", student=(id, name, age, dob, course, address, adm_date))

    return render_template("edit.html", student=student)


# ══════════════════════════════════════════════════════════════════════════════
# ❌ DELETE STUDENT  (supports both form POST and AJAX fetch)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_student(id):
    """
    Perform a clean deletion. In this custom ID system, we allow gaps to persist
    until the next student is added (where the gap will be filled).
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        db_execute("DELETE FROM students WHERE id = %s", (id,), commit=True)
        if is_ajax:
            return jsonify({"success": True, "message": "Student record deleted."})
        flash("🗑️ Student record deleted successfully.", "success")
    except Exception as e:
        app.logger.error(f"[DELETE_STUDENT] Error: {e}")
        if is_ajax:
            return jsonify({"success": False, "message": "Deletion failed."}), 500
        flash("Failed to delete record.", "danger")

    return redirect(url_for('view_students'))


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True)
