import csv
from re import search
from flask import Response
from flask import Blueprint, render_template, request, redirect, url_for, session
from extensions import mysql
import bcrypt
from flask_mail import Message
from extensions import mail

auth = Blueprint("auth", __name__)

# ==============================
# REGISTER
# ==============================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        hashed_pw = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO users (name,email,password,role)
            VALUES (%s,%s,%s,%s)
        """, (name, email, hashed_pw, role))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ==============================
# LOGIN
# ==============================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            return "User not found!"

        stored_password = user[3]

        if not bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8")):
            return "Wrong Password!"

        session["user_id"] = user[0]
        session["role"] = user[4]

        if user[4] == "admin":
            return redirect(url_for("auth.admin_dashboard"))

        elif user[4] == "organizer":
            return redirect(url_for("auth.organizer_dash"))

        else:
            return redirect(url_for("auth.student_dash"))

    return render_template("login.html")


# ==============================
# LOGOUT
# ==============================

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# ==============================
# CREATE EVENT
# ==============================

@auth.route("/create-event", methods=["GET", "POST"])
def create_event():

    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        date = request.form["date"]
        location = request.form["location"]

        cur = mysql.connection.cursor()

        cur.execute("""
            INSERT INTO events 
            (title, description, date, location, organizer_id, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
        """, (title, description, date, location, session["user_id"]))


        mysql.connection.commit()
        cur.close()

        return redirect(url_for("auth.manage_events"))

    return render_template("create_event.html")


# ==============================
# MANAGE EVENTS
# ==============================

@auth.route("/manage-events")
def manage_events():

    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT 
        events.id,
        events.title,
        events.date,
        events.location,
        COUNT(registrations.id) AS total_students,
        events.is_closed

    FROM events

    LEFT JOIN registrations 
        ON events.id = registrations.event_id

    WHERE events.organizer_id = %s

    GROUP BY 
        events.id,
        events.title,
        events.date,
        events.location,
        events.is_closed

    ORDER BY events.date DESC
""", (session["user_id"],))

    events = cur.fetchall()
    print(events[0])
    cur.close()

    return render_template("manage_events.html", events=events)


# ==============================
# DELETE EVENT
# ==============================

@auth.route("/delete-event/<int:event_id>")
def delete_event(event_id):

    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        DELETE FROM events 
        WHERE id=%s AND organizer_id=%s
    """, (event_id, session["user_id"]))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for("auth.manage_events"))


# ==============================
# EDIT EVENT
# ==============================

@auth.route("/edit-event/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):

    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        date = request.form["date"]
        location = request.form["location"]

        cur.execute("""
            UPDATE events
            SET title=%s, description=%s, date=%s, location=%s
            WHERE id=%s AND organizer_id=%s
        """, (title, description, date, location, event_id, session["user_id"]))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for("auth.manage_events"))

    cur.execute("""
        SELECT * FROM events
        WHERE id=%s AND organizer_id=%s
    """, (event_id, session["user_id"]))

    event = cur.fetchone()
    cur.close()

    return render_template("edit_event.html", event=event)


# ==============================
# STUDENT DASHBOARD
# ==============================

@auth.route("/student/dashboard")
def student_dash():

    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    # ✅ Count registered events
    cur.execute("""
        SELECT COUNT(*)
        FROM registrations
        WHERE student_id = %s
    """, (session["user_id"],))

    registered_count = cur.fetchone()[0]

    # ✅ Count TOTAL approved events
    cur.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE status='approved'
    """)

    total_events = cur.fetchone()[0]

    cur.close()

    return render_template(
        "student/dashboard.html",
        registered_count=registered_count,
        total_events=total_events
    )
# ==============================
# STUDENT EVENTS
# ==============================

@auth.route("/student/events")
def student_events():

    # 🔐 Security check
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("auth.login"))

    # ✅ Get search safely
    search = request.args.get("search", "").strip()

    cur = mysql.connection.cursor()

    # ✅ BASE QUERY (always runs)
    query = """
    SELECT 
        e.id,
        e.title,
        e.description,
        e.date,
        e.location,
        e.max_seats,

        COUNT(r.id) AS booked,

        EXISTS(
            SELECT 1
            FROM registrations r2
            WHERE r2.event_id = e.id
            AND r2.student_id = %s
        ) AS registered

    FROM events e

    LEFT JOIN registrations r
        ON e.id = r.event_id

    WHERE 
    e.status = 'approved'
    AND e.is_closed = FALSE
    """

    params = [session["user_id"]]

    # ✅ ONLY add search filter if user typed something
    if search:
        query += """
        AND (
            e.title LIKE %s
            OR e.location LIKE %s
        )
        """
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    # ✅ Finish query
    query += """
    GROUP BY 
        e.id, e.title, e.description, e.date, e.location, e.max_seats

    ORDER BY e.date ASC
    """

    cur.execute(query, tuple(params))
    events = cur.fetchall()
    cur.close()

    # ✅ Calculate seats left
    updated_events = []

    for event in events:

        event = list(event)

        max_seats = int(event[5])
        booked = int(event[6])

        seats_left = max_seats - booked

        event.append(seats_left)

        updated_events.append(event)

    return render_template(
        "student/events.html",
        events=updated_events,
        search=search   # ⭐ keeps search text in box
    )
# ==============================
# REGISTER EVENT
# ==============================
@auth.route("/register-event/<int:event_id>")
def register_event(event_id):

    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    # Check event approval
    cur.execute("""
        SELECT title, status 
        FROM events 
        WHERE id=%s
    """, (event_id,))

    event = cur.fetchone()

    if not event:
        cur.close()
        return "Event not found!"

    if event[1] != "approved":
        cur.close()
        return "Event not approved yet!"

    event_title = event[0]

    # Prevent duplicate
    cur.execute("""
        SELECT id 
        FROM registrations
        WHERE student_id=%s AND event_id=%s
    """, (session["user_id"], event_id))

    if cur.fetchone():
        cur.close()
        return redirect(url_for("auth.student_events"))

    # ✅ CHECK SEAT AVAILABILITY
    cur.execute("""
        SELECT max_seats,
               (SELECT COUNT(*) 
                FROM registrations 
                WHERE event_id=%s) AS booked
        FROM events
        WHERE id=%s
    """, (event_id, event_id))

    seat_data = cur.fetchone()

    max_seats = seat_data[0]
    booked = seat_data[1]

    if booked >= max_seats:
        cur.close()
        return "Sorry! This event is full."

    # Insert registration
    cur.execute("""
        INSERT INTO registrations (student_id, event_id)
        VALUES (%s,%s)
    """, (session["user_id"], event_id))

    mysql.connection.commit()

    # Fetch email
    cur.execute("""
        SELECT email 
        FROM users 
        WHERE id=%s
    """, (session["user_id"],))

    data = cur.fetchone()
    cur.close()

    if not data:
        return redirect(url_for("auth.student_events"))

    student_email = data[0]

    # SEND MAIL AFTER DB CLOSE
    try:
        msg = Message(
            subject="Event Registration Successful 🎉",
            recipients=[student_email]
        )

        msg.body = f"""
Hello Student,

You have successfully registered for:

👉 {event_title}

Please be present on time.

Thank you,
College Event Portal
"""

        mail.send(msg)

    except Exception as e:
        print("Mail error:", e)

    return redirect(url_for("auth.student_events"))






        
# ==============================
# VIEW REGISTRATIONS
# ==============================

@auth.route("/event/<int:event_id>/registrations")
def view_registrations(event_id):

    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT users.name, users.email, registrations.registered_at
        FROM registrations
        JOIN users ON users.id = registrations.student_id
        JOIN events ON events.id = registrations.event_id
        WHERE events.id = %s
        AND events.organizer_id = %s
    """, (event_id, session["user_id"]))

    students = cur.fetchall()
    cur.close()

    return render_template("view_registrations.html", students=students)


# ==============================
# ORGANIZER DASHBOARD
# ==============================

@auth.route("/organizer/dashboard")
def organizer_dash():

    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM events WHERE organizer_id=%s", (session["user_id"],))
    total_events = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE e.organizer_id=%s
    """, (session["user_id"],))
    total_registrations = cur.fetchone()[0]

    cur.execute("""
        SELECT e.title, COUNT(r.id) as total
        FROM events e
        LEFT JOIN registrations r ON e.id = r.event_id
        WHERE e.organizer_id=%s
        GROUP BY e.id
        ORDER BY total DESC
        LIMIT 1
    """ ,(session["user_id"],))

    popular_event = cur.fetchone()
    cur.close()

    return render_template(
        "organizer/dashboard.html",
        total_events=total_events,
        total_registrations=total_registrations,
        popular_event=popular_event
    )


# ==============================
# ADMIN DASHBOARD
# ==============================

@auth.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM users WHERE role='organizer'")
    total_organizers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM events")
    total_events = cur.fetchone()[0]

    cur.close()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_organizers=total_organizers,
        total_events=total_events
    )


# ==============================
# ADMIN ANALYTICS
# ==============================

@auth.route("/admin/analytics")
def admin_analytics():

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM events")
    total_events = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM registrations")
    total_registrations = cur.fetchone()[0]

    cur.execute("""
        SELECT events.title, COUNT(registrations.id) as total
        FROM events
        LEFT JOIN registrations 
            ON events.id = registrations.event_id
        GROUP BY events.id
        ORDER BY total DESC
        LIMIT 1
    """)

    popular_event = cur.fetchone()
    cur.close()

    return render_template(
        "admin_analytics.html",
        total_events=total_events,
        total_registrations=total_registrations,
        popular_event=popular_event
    )
@auth.route("/admin/students")
def admin_students():

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, name, email
        FROM users
        WHERE role='student'
        ORDER BY id DESC
    """)

    students = cur.fetchall()
    cur.close()

    return render_template("admin/admin_students.html", students=students)

@auth.route("/admin/organizers")
def admin_organizers():

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT id, name, email
        FROM users
        WHERE role='organizer'
        ORDER BY id DESC
    """)

    organizers = cur.fetchall()
    cur.close()

    return render_template("admin/admin_organizers.html", organizers=organizers)
@auth.route("/admin/events")
def admin_events():

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            events.id,
            events.title,
            users.name,
            events.date,
            events.status
        FROM events
        JOIN users 
            ON users.id = events.organizer_id
        ORDER BY events.date DESC
    """)

    events = cur.fetchall()
    cur.close()

    return render_template("admin/admin_events.html", events=events)

@auth.route("/admin/approve-event/<int:event_id>")
def approve_event(event_id):

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    # Approve event
    cur.execute("""
        UPDATE events
        SET status='approved'
        WHERE id=%s
    """, (event_id,))

    # Get students emails
    cur.execute("""
        SELECT users.email, events.title
        FROM registrations
        JOIN users ON users.id = registrations.student_id
        JOIN events ON events.id = registrations.event_id
        WHERE events.id=%s
    """, (event_id,))

    students = cur.fetchall()

    mysql.connection.commit()
    cur.close()

    
    return redirect(url_for("auth.admin_events"))

@auth.route("/admin/reject-event/<int:event_id>")
def reject_event(event_id):

    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE events
        SET status='rejected'
        WHERE id=%s
    """, (event_id,))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for("auth.admin_events"))
@auth.route("/student/my-events")
def my_events():

    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            e.title,
            e.description,
            e.date,
            e.location
        FROM registrations r
        JOIN events e
            ON e.id = r.event_id
        WHERE r.student_id = %s
        ORDER BY e.date ASC
    """, (session["user_id"],))

    events = cur.fetchall()
    cur.close()

    return render_template("student/my_events.html", events=events)
@auth.route("/cancel-registration/<int:event_id>")
def cancel_registration(event_id):

    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        DELETE FROM registrations
        WHERE student_id=%s AND event_id=%s
    """, (session["user_id"], event_id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for("auth.student_events"))
@auth.route("/download-participants/<int:event_id>")
def download_participants(event_id):

    # Security check
    if "user_id" not in session or session.get("role") != "organizer":
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT users.name, users.email, registrations.registered_at
        FROM registrations
        JOIN users ON users.id = registrations.student_id
        JOIN events ON events.id = registrations.event_id
        WHERE events.id=%s
        AND events.organizer_id=%s
    """, (event_id, session["user_id"]))

    students = cur.fetchall()
    cur.close()

    # Create CSV
    def generate():
        data = csv.writer(open("participants.csv", "w", newline=''))

    # Better approach — stream directly:
    def generate_csv():
        yield "Name,Email,Registered At\n"

        for student in students:
            row = f"{student[0]},{student[1]},{student[2]}\n"
            yield row

    return Response(
        generate_csv(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            f"attachment; filename=participants_event_{event_id}.csv"
        }
    )
@auth.route("/toggle-registration/<int:event_id>")
def toggle_registration(event_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    cur = mysql.connection.cursor()

    # Flip the boolean
    cur.execute("""
        UPDATE events
        SET is_closed = NOT is_closed
        WHERE id=%s
    """, (event_id,))

    mysql.connection.commit()
    cur.close()

    return redirect("/manage-events")