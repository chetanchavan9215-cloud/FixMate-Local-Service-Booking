from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)

app.secret_key = "fixmate_secret_key"

DATABASE = "fixmate.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE SETUP
# =========================================================

def setup_database():

    conn = get_db()
    cur = conn.cursor()

    # =====================================================
    # USERS TABLE
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    # =====================================================
    # BOOKINGS TABLE
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            address TEXT,
            service TEXT,
            user_id INTEGER,
            status TEXT DEFAULT 'Pending',
            date TEXT,
            time TEXT,
            provider_id INTEGER,
            provider_status TEXT DEFAULT 'Unassigned',
            latitude REAL,
            longitude REAL
        )
    """)

    # =====================================================
    # PROVIDERS TABLE
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            service TEXT,
            password TEXT
        )
    """)

    # =====================================================
    # CHECK BOOKINGS COLUMNS
    # =====================================================

    cur.execute("PRAGMA table_info(bookings)")

    booking_columns = [
        row[1]
        for row in cur.fetchall()
    ]

    if "user_id" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN user_id INTEGER
        """)

    if "status" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN status TEXT DEFAULT 'Pending'
        """)

    if "date" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN date TEXT
        """)

    if "time" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN time TEXT
        """)

    if "provider_id" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN provider_id INTEGER
        """)

    if "provider_status" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN provider_status TEXT DEFAULT 'Unassigned'
        """)

    if "rejected_by_provider_id" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN rejected_by_provider_id INTEGER
        """)

    # =====================================================
    # LOCATION COLUMNS
    # =====================================================

    if "latitude" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN latitude REAL
        """)

    if "longitude" not in booking_columns:

        cur.execute("""
            ALTER TABLE bookings
            ADD COLUMN longitude REAL
        """)

    # =====================================================
    # CHECK PROVIDER COLUMNS
    # =====================================================

    cur.execute("PRAGMA table_info(providers)")

    provider_columns = [
        row[1]
        for row in cur.fetchall()
    ]

    if "name" not in provider_columns:

        cur.execute("""
            ALTER TABLE providers
            ADD COLUMN name TEXT
        """)

    if "email" not in provider_columns:

        cur.execute("""
            ALTER TABLE providers
            ADD COLUMN email TEXT
        """)

    if "phone" not in provider_columns:

        cur.execute("""
            ALTER TABLE providers
            ADD COLUMN phone TEXT
        """)

    if "service" not in provider_columns:

        cur.execute("""
            ALTER TABLE providers
            ADD COLUMN service TEXT
        """)

    if "password" not in provider_columns:

        cur.execute("""
            ALTER TABLE providers
            ADD COLUMN password TEXT
        """)

    # =====================================================
    # FIX OLD BOOKING PROVIDER STATUS
    # =====================================================

    cur.execute("""
        UPDATE bookings
        SET provider_status='Completed', rejected_by_provider_id=NULL
        WHERE status='Completed'
        AND provider_id IS NOT NULL
        AND (
            provider_status IS NULL
            OR provider_status='Unassigned'
        )
    """)

    cur.execute("""
        UPDATE bookings
        SET provider_status='Cancelled'
        WHERE status='Cancelled'
        AND (
            provider_status IS NULL
            OR provider_status='Unassigned'
        )
    """)

    conn.commit()
    conn.close()


setup_database()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# CUSTOMER LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        # ADMIN LOGIN
        if email == "admin@fixmate.com" and password == "admin123":

            session.clear()

            session["admin"] = True

            flash("Admin Login Successful!", "success")
            return redirect("/admin")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM users
            WHERE LOWER(email)=?
            AND password=?
        """, (
            email,
            password
        ))

        user = cur.fetchone()

        conn.close()

        if user:

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            flash("Login Successful!", "success")
            return redirect("/dashboard")

        flash(
            "Invalid Email or Password.",
            "error"
        )

    return render_template("login.html")


# =========================================================
# CUSTOMER REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not name or not email or not password:

            flash(
                "Please fill all fields.",
                "error"
            )

            return redirect("/register")

        conn = get_db()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO users
                (
                    name,
                    email,
                    password
                )
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                password
            ))

            conn.commit()
            conn.close()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()

            flash(
                "Email already registered.",
                "error"
            )

            return redirect("/register")

    return render_template("register.html")


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE user_id=?
    """, (
        user_id,
    ))

    total_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE user_id=?
        AND status='Pending'
    """, (
        user_id,
    ))

    pending_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE user_id=?
        AND status='Completed'
    """, (
        user_id,
    ))

    completed_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE user_id=?
        AND status='Cancelled'
    """, (
        user_id,
    ))

    cancelled_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT
            id,
            service,
            date,
            time,
            status
        FROM bookings
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 5
    """, (
        user_id,
    ))

    recent_bookings = cur.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User"),
        user_email=session.get("user_email", ""),
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        completed_bookings=completed_bookings,
        cancelled_bookings=cancelled_bookings,
        recent_bookings=recent_bookings
    )


# =========================================================
# CUSTOMER PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM users
        WHERE id=?
    """, (
        session["user_id"],
    ))

    user = cur.fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# EDIT CUSTOMER PROFILE
# =========================================================

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()

        try:

            cur.execute("""
                UPDATE users
                SET
                    name=?,
                    email=?
                WHERE id=?
            """, (
                name,
                email,
                session["user_id"]
            ))

            conn.commit()

            session["user_name"] = name
            session["user_email"] = email

            conn.close()

            flash(
                "Profile updated successfully.",
                "success"
            )

            return redirect("/profile")

        except sqlite3.IntegrityError:

            conn.close()

            flash(
                "This email is already registered.",
                "error"
            )

            return redirect("/edit-profile")

    cur.execute("""
        SELECT *
        FROM users
        WHERE id=?
    """, (
        session["user_id"],
    ))

    user = cur.fetchone()

    conn.close()

    return render_template(
        "edit_profile.html",
        user=user
    )


# =========================================================
# CHANGE CUSTOMER PASSWORD
# =========================================================

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        old_password = request.form.get("old_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT password
            FROM users
            WHERE id=?
        """, (
            session["user_id"],
        ))

        user = cur.fetchone()

        if not user or user["password"] != old_password:

            conn.close()

            flash(
                "Old password is incorrect.",
                "error"
            )

            return redirect("/change-password")

        if new_password != confirm_password:

            conn.close()

            flash(
                "New passwords do not match.",
                "error"
            )

            return redirect("/change-password")

        cur.execute("""
            UPDATE users
            SET password=?
            WHERE id=?
        """, (
            new_password,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect("/profile")

    return render_template(
        "change_password.html"
    )


# =========================================================
# BOOK SERVICE
# =========================================================

@app.route("/book", methods=["GET", "POST"])
def book():

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        service = (request.form.get("service") or "").strip()
        date = request.form.get("date") or ""
        time = request.form.get("time") or ""

        # =================================================
        # LOCATION
        # =================================================

        latitude_value = (
            request.form.get("latitude") or ""
        ).strip()

        longitude_value = (
            request.form.get("longitude") or ""
        ).strip()

        latitude = None
        longitude = None

        # Convert location values to numbers safely.
        try:

            if latitude_value:
                latitude = float(latitude_value)

            if longitude_value:
                longitude = float(longitude_value)

        except ValueError:

            flash(
                "Invalid service location selected.",
                "error"
            )

            return redirect("/book")

        # =================================================
        # REQUIRED BOOKING FIELDS
        # =================================================

        if not all([
            name,
            phone,
            address,
            service,
            date,
            time
        ]):

            flash(
                "Please fill all booking fields.",
                "error"
            )

            return redirect("/book")

        # =================================================
        # LOCATION VALIDATION
        # =================================================

        if latitude is None or longitude is None:

            flash(
                "Please select your service location on the map.",
                "error"
            )

            return redirect("/book")

        # Valid latitude range
        if latitude < -90 or latitude > 90:

            flash(
                "Invalid latitude.",
                "error"
            )

            return redirect("/book")

        # Valid longitude range
        if longitude < -180 or longitude > 180:

            flash(
                "Invalid longitude.",
                "error"
            )

            return redirect("/book")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO bookings
            (
                name,
                phone,
                address,
                service,
                user_id,
                status,
                date,
                time,
                provider_id,
                provider_status,
                latitude,
                longitude
            )
            VALUES (
                ?, ?, ?, ?, ?,
                'Pending',
                ?, ?,
                NULL,
                'Unassigned',
                ?, ?
            )
        """, (
            name,
            phone,
            address,
            service,
            session["user_id"],
            date,
            time,
            latitude,
            longitude
        ))

        booking_id = cur.lastrowid

        conn.commit()
        conn.close()

        return redirect(
            f"/confirmation/{booking_id}"
        )

    return render_template(
        "booking.html"
    )


# =========================================================
# BOOKING CONFIRMATION
# =========================================================

@app.route("/confirmation/<int:id>")
def confirmation(id):

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM bookings
        WHERE id=?
        AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    booking = cur.fetchone()

    conn.close()

    if not booking:

        return redirect("/mybookings")

    return render_template(
        "confirmation.html",
        booking=booking
    )


# =========================================================
# MY BOOKINGS
# =========================================================

@app.route("/mybookings")
def mybookings():

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    search = request.args.get(
        "search",
        ""
    )

    status = request.args.get(
        "status",
        ""
    )

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT *
        FROM bookings
        WHERE user_id=?
    """

    params = [
        session["user_id"]
    ]

    if search:

        query += """
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR service LIKE ?
                OR address LIKE ?
            )
        """

        value = "%" + search + "%"

        params.extend([
            value,
            value,
            value,
            value
        ])

    if status:

        query += """
            AND status=?
        """

        params.append(status)

    query += """
        ORDER BY id DESC
    """

    cur.execute(
        query,
        params
    )

    bookings = cur.fetchall()

    conn.close()

    return render_template(
        "mybookings.html",
        bookings=bookings,
        search=search,
        status=status
    )


# =========================================================
# BOOKING DETAILS
# =========================================================

@app.route("/booking/<int:id>")
def booking_details(id):

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.*,
            p.name AS provider_name,
            p.phone AS provider_phone,
            p.email AS provider_email
        FROM bookings b
        LEFT JOIN providers p
            ON CAST(b.provider_id AS INTEGER)=p.id
        WHERE b.id=?
        AND b.user_id=?
    """, (
        id,
        session["user_id"]
    ))

    booking = cur.fetchone()

    conn.close()

    if not booking:

        return redirect("/mybookings")

    return render_template(
        "booking_details.html",
        booking=booking
    )


# =========================================================
# EDIT BOOKING
# =========================================================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_booking(id):

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM bookings
        WHERE id=?
        AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    booking = cur.fetchone()

    if not booking:

        conn.close()

        return redirect("/mybookings")

    if booking["status"] != "Pending":

        conn.close()

        flash(
            "Only pending bookings can be edited.",
            "error"
        )

        return redirect(
            f"/booking/{id}"
        )

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        service = (request.form.get("service") or "").strip()
        date = request.form.get("date") or ""
        time = request.form.get("time") or ""

        # =================================================
        # LOCATION
        # =================================================

        latitude_value = (
            request.form.get("latitude") or ""
        ).strip()

        longitude_value = (
            request.form.get("longitude") or ""
        ).strip()

        latitude = None
        longitude = None

        try:

            if latitude_value:
                latitude = float(latitude_value)

            if longitude_value:
                longitude = float(longitude_value)

        except ValueError:

            conn.close()

            flash(
                "Invalid service location selected.",
                "error"
            )

            return redirect(
                f"/edit/{id}"
            )

        # If no new location was selected,
        # keep the existing location.
        if latitude is None:
            latitude = booking["latitude"]

        if longitude is None:
            longitude = booking["longitude"]

        if latitude is None or longitude is None:

            conn.close()

            flash(
                "Please select your service location on the map.",
                "error"
            )

            return redirect(
                f"/edit/{id}"
            )

        if latitude < -90 or latitude > 90:

            conn.close()

            flash(
                "Invalid latitude.",
                "error"
            )

            return redirect(
                f"/edit/{id}"
            )

        if longitude < -180 or longitude > 180:

            conn.close()

            flash(
                "Invalid longitude.",
                "error"
            )

            return redirect(
                f"/edit/{id}"
            )

        cur.execute("""
            UPDATE bookings
            SET
                name=?,
                phone=?,
                address=?,
                service=?,
                date=?,
                time=?,
                latitude=?,
                longitude=?,
                provider_id=NULL,
                provider_status='Unassigned',
                rejected_by_provider_id=NULL
            WHERE id=?
            AND user_id=?
            AND status='Pending'
        """, (
            name,
            phone,
            address,
            service,
            date,
            time,
            latitude,
            longitude,
            id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash(
            "Booking updated successfully.",
            "success"
        )

        return redirect(
            f"/booking/{id}"
        )

    conn.close()

    return render_template(
        "edit_booking.html",
        booking=booking
    )


# =========================================================
# CANCEL BOOKING
# =========================================================

@app.route("/cancel/<int:id>")
def cancel_booking(id):

    if session.get("admin"):

        return redirect("/admin")

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            status,
            provider_status
        FROM bookings
        WHERE id=?
        AND user_id=?
    """, (
        id,
        session["user_id"]
    ))

    booking = cur.fetchone()

    if not booking:

        conn.close()

        flash(
            "Booking not found.",
            "error"
        )

        return redirect("/mybookings")

    current_status = booking["status"]
    provider_status = booking["provider_status"]

    if (
        current_status == "Pending"
        and provider_status in [
            "Unassigned",
            "Assigned",
            "Rejected"
        ]
    ):

        cur.execute("""
            UPDATE bookings
            SET
                status='Cancelled',
                provider_status='Cancelled'
            WHERE id=?
            AND user_id=?
        """, (
            id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash(
            "Booking cancelled successfully.",
            "success"
        )

        return redirect("/mybookings")

    conn.close()

    flash(
        "This booking cannot be cancelled now.",
        "error"
    )

    return redirect("/mybookings")


# =========================================================
# SERVICE PROVIDER REGISTER
# =========================================================

@app.route(
    "/provider/register",
    methods=["GET", "POST"]
)
def provider_register():

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()

        email = (
            request.form.get("email") or ""
        ).strip().lower()

        phone = (
            request.form.get("phone") or ""
        ).strip()

        service = (
            request.form.get("service") or ""
        ).strip()

        password = (
            request.form.get("password") or ""
        )

        confirm_password = (
            request.form.get("confirm_password") or ""
        )

        # -------------------------------------------------
        # REQUIRED FIELDS
        # -------------------------------------------------

        if not all([
            name,
            email,
            phone,
            service,
            password,
            confirm_password
        ]):

            flash(
                "Please fill all provider registration fields.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

        # -------------------------------------------------
        # PASSWORD CHECK
        # -------------------------------------------------

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

        # -------------------------------------------------
        # PHONE CHECK
        # -------------------------------------------------

        if not phone.isdigit() or len(phone) != 10:

            flash(
                "Please enter a valid 10-digit mobile number.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

        # -------------------------------------------------
        # PASSWORD LENGTH
        # -------------------------------------------------

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

        conn = get_db()
        cur = conn.cursor()

        # -------------------------------------------------
        # CHECK EXISTING PROVIDER
        # -------------------------------------------------

        cur.execute("""
            SELECT id
            FROM providers
            WHERE LOWER(email)=?
        """, (
            email,
        ))

        existing_provider = cur.fetchone()

        if existing_provider:

            conn.close()

            flash(
                "This email is already registered as a provider.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

        # -------------------------------------------------
        # INSERT PROVIDER
        # -------------------------------------------------

        try:

            cur.execute("""
                INSERT INTO providers
                (
                    name,
                    email,
                    phone,
                    service,
                    password
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                email,
                phone,
                service,
                password
            ))

            conn.commit()
            conn.close()

            flash(
                "Service Provider registration successful. Please login.",
                "success"
            )

            return redirect(
                "/provider/login"
            )

        except sqlite3.IntegrityError:

            conn.rollback()
            conn.close()

            flash(
                "This provider email is already registered.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

        except Exception as e:

            conn.rollback()
            conn.close()

            print(
                "Provider Registration Error:",
                e
            )

            flash(
                "Provider registration failed. Please try again.",
                "error"
            )

            return redirect(
                "/provider/register"
            )

    return render_template(
        "provider_register.html"
    )


# =========================================================
# SERVICE PROVIDER LOGIN
# =========================================================

@app.route(
    "/provider/login",
    methods=["GET", "POST"]
)
def provider_login():

    if request.method == "POST":

        email = (
            request.form.get("email") or ""
        ).strip().lower()

        password = (
            request.form.get("password") or ""
        )

        if not email or not password:

            flash(
                "Please enter email and password.",
                "error"
            )

            return redirect(
                "/provider/login"
            )

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                name,
                email,
                phone,
                service,
                password
            FROM providers
            WHERE LOWER(email)=?
            AND password=?
        """, (
            email,
            password
        ))

        provider = cur.fetchone()

        conn.close()

        if provider:

            session.clear()

            session["provider_id"] = provider["id"]
            session["provider_name"] = provider["name"]
            session["provider_email"] = provider["email"]
            session["provider_phone"] = provider["phone"]
            session["provider_service"] = provider["service"]

            flash("Provider Login Successful!", "success")
            return redirect(
                "/provider/dashboard"
            )

        flash(
            "Invalid Provider Email or Password.",
            "error"
        )

        return redirect(
            "/provider/login"
        )

    return render_template(
        "provider_login.html"
    )


# =========================================================
# SERVICE PROVIDER DASHBOARD
# =========================================================

@app.route("/provider/dashboard")
def provider_dashboard():

    if "provider_id" not in session:

        return redirect(
            "/provider/login"
        )

    provider_id = session["provider_id"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            name,
            phone,
            address,
            service,
            date,
            time,
            status,
            provider_status,
            latitude,
            longitude
        FROM bookings
        WHERE provider_id=?
           OR rejected_by_provider_id=?
        ORDER BY id DESC
    """, (
        provider_id,
        provider_id,
    ))

    rows = cur.fetchall()

    bookings = []

    for row in rows:

        bookings.append({
            "id": row["id"],
            "name": row["name"],
            "phone": row["phone"],
            "address": row["address"],
            "service": row["service"],
            "date": row["date"],
            "time": row["time"],
            "status": row["status"],
            "provider_status": row["provider_status"],
            "latitude": row["latitude"],
            "longitude": row["longitude"]
        })

    total_bookings = len(bookings)

    accepted_bookings = sum(
        1
        for booking in bookings
        if booking["provider_status"] == "Accepted"
    )

    completed_bookings = sum(
        1
        for booking in bookings
        if booking["provider_status"] == "Completed"
    )

    rejected_bookings = sum(
        1
        for booking in bookings
        if booking["provider_status"] == "Rejected"
    )

    conn.close()

    return render_template(
        "provider_dashboard.html",
        provider_name=session["provider_name"],
        provider_service=session["provider_service"],
        total_bookings=total_bookings,
        accepted_bookings=accepted_bookings,
        completed_bookings=completed_bookings,
        rejected_bookings=rejected_bookings,
        bookings=bookings
    )


# =========================================================
# PROVIDER ACCEPT BOOKING
# =========================================================

@app.route(
    "/provider/accept/<int:id>",
    methods=["POST"]
)
def provider_accept(id):

    if "provider_id" not in session:

        return redirect(
            "/provider/login"
        )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE bookings
        SET provider_status='Accepted', rejected_by_provider_id=NULL
        WHERE id=?
        AND provider_id=?
        AND status='Pending'
        AND provider_status='Assigned'
    """, (
        id,
        session["provider_id"]
    ))

    if cur.rowcount == 0:

        conn.close()

        flash(
            "Booking could not be accepted. This booking may not be assigned to you.",
            "error"
        )

        return redirect(
            "/provider/dashboard"
        )

    conn.commit()
    conn.close()

    flash(
        "Booking accepted successfully.",
        "success"
    )

    return redirect(
        "/provider/dashboard"
    )


# =========================================================
# PROVIDER REJECT BOOKING
# =========================================================

@app.route(
    "/provider/reject/<int:id>",
    methods=["POST"]
)
def provider_reject(id):

    if "provider_id" not in session:

        return redirect(
            "/provider/login"
        )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE bookings
        SET
            provider_status='Rejected',
            provider_id=NULL,
            rejected_by_provider_id=?
        WHERE id=?
        AND provider_id=?
        AND status='Pending'
        AND provider_status='Assigned'
    """, (
        session["provider_id"],
        id,
        session["provider_id"]
    ))

    if cur.rowcount == 0:

        conn.close()

        flash(
            "Booking could not be rejected.",
            "error"
        )

        return redirect(
            "/provider/dashboard"
        )

    conn.commit()
    conn.close()

    flash(
        "Booking rejected. Admin can assign another provider.",
        "success"
    )

    return redirect(
        "/provider/dashboard"
    )


# =========================================================
# PROVIDER COMPLETE SERVICE
# =========================================================

@app.route(
    "/provider/completed/<int:id>",
    methods=["POST"]
)
def provider_completed(id):

    if "provider_id" not in session:

        return redirect(
            "/provider/login"
        )

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE bookings
        SET provider_status='Completed'
        WHERE id=?
        AND provider_id=?
        AND status='Pending'
        AND provider_status='Accepted'
    """, (
        id,
        session["provider_id"]
    ))

    if cur.rowcount == 0:

        conn.close()

        flash(
            "Service could not be marked completed. Provider must accept the booking first.",
            "error"
        )

        return redirect(
            "/provider/dashboard"
        )

    conn.commit()
    conn.close()

    flash(
        "Service completed. Waiting for admin confirmation.",
        "success"
    )

    return redirect(
        "/provider/dashboard"
    )


# =========================================================
# PROVIDER LOGOUT
# =========================================================

@app.route("/provider/logout")
def provider_logout():

    session.clear()

    flash("Provider Logout Successful!", "success")
    return redirect("/login")


# =========================================================
# ADMIN LOGIN + DASHBOARD
# =========================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin():

    if request.method == "POST":

        email = (
            request.form.get("email") or ""
        ).strip().lower()

        password = (
            request.form.get("password") or ""
        )

        if (
            email == "admin@fixmate.com"
            and password == "admin123"
        ):

            session.clear()

            session["admin"] = True

            return redirect(
                "/admin"
            )

        flash(
            "Invalid Admin Email or Password.",
            "error"
        )

        return redirect(
            "/admin"
        )

    if not session.get("admin"):

        return render_template(
            "admin_login.html"
        )

    search = request.args.get(
        "search",
        ""
    )

    status_filter = request.args.get(
        "status",
        ""
    )

    conn = get_db()
    cur = conn.cursor()

    # =====================================================
    # BOOKINGS
    # =====================================================

    query = """
        SELECT
            id,
            name,
            phone,
            address,
            service,
            user_id,
            status,
            date,
            time,
            provider_id,
            provider_status,
            latitude,
            longitude
        FROM bookings
        WHERE 1=1
    """

    params = []

    if search:

        query += """
            AND (
                name LIKE ?
                OR phone LIKE ?
                OR service LIKE ?
                OR address LIKE ?
            )
        """

        value = "%" + search + "%"

        params.extend([
            value,
            value,
            value,
            value
        ])

    if status_filter:

        query += """
            AND LOWER(TRIM(COALESCE(status, 'Pending'))) = LOWER(TRIM(?))
        """

        params.append(
            status_filter
        )

    query += """
        ORDER BY id DESC
    """

    cur.execute(
        query,
        params
    )

    bookings = cur.fetchall()

    # Repair old/legacy rows which may have NULL status values.
    cur.execute("""
        UPDATE bookings
        SET status='Pending'
        WHERE status IS NULL
           OR TRIM(status)=''
    """)

    cur.execute("""
        UPDATE bookings
        SET provider_status='Unassigned'
        WHERE provider_status IS NULL
           OR TRIM(provider_status)=''
    """)

    conn.commit()

    # Fetch again after the small legacy-data repair.
    cur.execute(
        query,
        params
    )

    bookings = cur.fetchall()

    # =====================================================
    # PROVIDERS
    # =====================================================

    cur.execute("""
        SELECT
            id,
            name,
            phone,
            email,
            service
        FROM providers
        ORDER BY name ASC
    """)

    provider_rows = cur.fetchall()

    providers = []

    for provider in provider_rows:

        providers.append({
            "id": provider["id"],
            "name": provider["name"],
            "phone": provider["phone"],
            "email": provider["email"],
            "service": provider["service"]
        })

    # =====================================================
    # STATISTICS
    # =====================================================

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
    """)

    total_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status='Pending'
    """)

    pending_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status='Completed'
    """)

    completed_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE status='Cancelled'
    """)

    cancelled_bookings = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    total_users = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM providers
    """)

    total_providers = cur.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        bookings=bookings,
        providers=providers,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        completed_bookings=completed_bookings,
        cancelled_bookings=cancelled_bookings,
        total_users=total_users,
        total_providers=total_providers,
        search=search,
        status_filter=status_filter,
        status=status_filter
    )


# =========================================================
# ADMIN BOOKING DETAILS
# =========================================================

@app.route("/admin/booking/<int:id>")
def admin_booking_details(id):

    if not session.get("admin"):

        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.*,
            p.name AS provider_name,
            p.phone AS provider_phone,
            p.email AS provider_email
        FROM bookings b
        LEFT JOIN providers p
            ON b.provider_id=p.id
        WHERE b.id=?
    """, (
        id,
    ))

    booking = cur.fetchone()

    conn.close()

    if not booking:

        return redirect("/admin")

    return render_template(
        "admin_booking_details.html",
        booking=booking
    )


# =========================================================
# ADMIN USERS
# =========================================================

@app.route("/admin/users")
def admin_users():

    if not session.get("admin"):

        return redirect("/admin")

    search = request.args.get(
        "search",
        ""
    )

    conn = get_db()
    cur = conn.cursor()

    if search:

        value = "%" + search + "%"

        cur.execute("""
            SELECT *
            FROM users
            WHERE name LIKE ?
            OR email LIKE ?
            ORDER BY id DESC
        """, (
            value,
            value
        ))

    else:

        cur.execute("""
            SELECT *
            FROM users
            ORDER BY id DESC
        """)

    users = cur.fetchall()

    conn.close()

    return render_template(
        "admin_users.html",
        users=users,
        search=search
    )


# =========================================================
# ADMIN DELETE USER
# =========================================================

@app.route("/admin/user/delete/<int:id>")
def admin_delete_user(id):

    if not session.get("admin"):

        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM bookings
        WHERE user_id=?
    """, (
        id,
    ))

    cur.execute("""
        DELETE FROM users
        WHERE id=?
    """, (
        id,
    ))

    conn.commit()
    conn.close()

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        "/admin/users"
    )


# =========================================================
# ADMIN ASSIGN PROVIDER
# =========================================================

@app.route(
    "/admin/assign-provider/<int:booking_id>",
    methods=["POST"]
)
@app.route(
    "/admin/assign/<int:booking_id>",
    methods=["POST"]
)
def admin_assign_provider(booking_id):

    if not session.get("admin"):

        return redirect("/admin")

    provider_id = request.form.get(
        "provider_id"
    )

    if not provider_id:

        flash(
            "Please select a provider.",
            "error"
        )

        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            service,
            status,
            provider_id,
            provider_status
        FROM bookings
        WHERE id=?
    """, (
        booking_id,
    ))

    booking = cur.fetchone()

    if not booking:

        conn.close()

        flash(
            "Booking not found.",
            "error"
        )

        return redirect("/admin")

    booking_service = booking["service"]
    booking_status = booking["status"]
    current_provider_status = booking["provider_status"]

    if booking_status == "Completed":

        conn.close()

        flash(
            "Completed booking cannot be assigned again.",
            "error"
        )

        return redirect("/admin")

    if booking_status == "Cancelled":

        conn.close()

        flash(
            "Cancelled booking cannot be assigned.",
            "error"
        )

        return redirect("/admin")

    if current_provider_status in [
        "Accepted",
        "Completed"
    ]:

        conn.close()

        flash(
            "Provider cannot be changed after acceptance/completion.",
            "error"
        )

        return redirect("/admin")

    cur.execute("""
        SELECT
            id,
            name,
            email,
            phone,
            service
        FROM providers
        WHERE id=?
    """, (
        provider_id,
    ))

    provider = cur.fetchone()

    if not provider:

        conn.close()

        flash(
            "Provider not found.",
            "error"
        )

        return redirect("/admin")

    provider_service = provider["service"]

    def normalize_service(value):

        return " ".join(
            (value or "")
            .strip()
            .lower()
            .split()
        )

    if normalize_service(provider_service) != normalize_service(
        booking_service
    ):

        conn.close()

        flash(
            f"Selected provider service is '{provider_service}', "
            f"but booking service is '{booking_service}'.",
            "error"
        )

        return redirect("/admin")

    cur.execute("""
        UPDATE bookings
        SET
            provider_id=?,
            provider_status='Assigned',
            status='Pending',
            rejected_by_provider_id=NULL
        WHERE id=?
    """, (
        provider_id,
        booking_id
    ))

    if cur.rowcount == 0:

        conn.close()

        flash(
            "Provider assignment failed.",
            "error"
        )

        return redirect("/admin")

    conn.commit()
    conn.close()

    flash(
        "Provider assigned successfully.",
        "success"
    )

    return redirect("/admin")


# =========================================================
# ADMIN STATUS UPDATE
# =========================================================

@app.route(
    "/admin/status/<int:id>",
    methods=["POST"]
)
def admin_status(id):

    if not session.get("admin"):

        return redirect("/admin")

    new_status = request.form.get(
        "status"
    )

    allowed_statuses = [
        "Pending",
        "Completed",
        "Cancelled"
    ]

    if new_status not in allowed_statuses:

        flash(
            "Invalid status.",
            "error"
        )

        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            status,
            provider_id,
            provider_status
        FROM bookings
        WHERE id=?
    """, (
        id,
    ))

    booking = cur.fetchone()

    if not booking:

        conn.close()

        flash(
            "Booking not found.",
            "error"
        )

        return redirect("/admin")

    provider_id = booking["provider_id"]
    provider_status = booking["provider_status"]

    if new_status == "Completed":

        if provider_id is None:

            conn.close()

            flash(
                "Cannot complete booking because no provider is assigned.",
                "error"
            )

            return redirect("/admin")

        if provider_status != "Completed":

            conn.close()

            flash(
                "Provider must complete the service before admin can complete the booking.",
                "error"
            )

            return redirect("/admin")

        cur.execute("""
            UPDATE bookings
            SET status='Completed'
            WHERE id=?
        """, (
            id,
        ))

    elif new_status == "Cancelled":

        if provider_status == "Accepted":

            conn.close()

            flash(
                "Cannot cancel. Provider has already accepted this booking.",
                "error"
            )

            return redirect("/admin")

        if provider_status == "Completed":

            conn.close()

            flash(
                "Cannot cancel. Provider has already completed the service.",
                "error"
            )

            return redirect("/admin")

        cur.execute("""
            UPDATE bookings
            SET
                status='Cancelled',
                provider_status='Cancelled'
            WHERE id=?
        """, (
            id,
        ))

    elif new_status == "Pending":

        cur.execute("""
            UPDATE bookings
            SET status='Pending'
            WHERE id=?
        """, (
            id,
        ))

    if cur.rowcount == 0:

        conn.close()

        flash(
            "Booking status could not be updated.",
            "error"
        )

        return redirect("/admin")

    conn.commit()
    conn.close()

    flash(
        "Booking status updated successfully.",
        "success"
    )

    return redirect("/admin")


# =========================================================
# ADMIN DELETE BOOKING
# =========================================================

@app.route("/admin/delete/<int:id>")
def admin_delete_booking(id):

    if not session.get("admin"):

        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM bookings
        WHERE id=?
    """, (
        id,
    ))

    conn.commit()
    conn.close()

    flash(
        "Booking deleted successfully.",
        "success"
    )

    return redirect("/admin")


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    flash("Admin Logout Successful!", "success")
    return redirect("/login")


# =========================================================
# CUSTOMER LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logout Successful!", "success")
    return redirect("/login")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )