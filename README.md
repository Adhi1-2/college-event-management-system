🎓 College Event Management System

A full-stack web application designed to manage college events efficiently with role-based access, seat-limited registrations, admin approvals, and real-time event control.

Built using Flask, MySQL, and Bootstrap, this system handles the complete event lifecycle — from creation and approval to student registration and organizer analytics.

🚀 Features
👤 Authentication & Roles

Secure login system with session management

Role-based access:

Admin

Organizer

Student

🛡️ Admin Panel

Approve or reject events submitted by organizers

View registered students and organizers

Maintain platform-level control

🧑‍🏫 Organizer Dashboard

Create and manage events

Edit or delete events

Close / Reopen event registrations dynamically

Auto-close registration when maximum seats are filled

View registered participants

Download participants list as CSV

Real-time registration count display

🎓 Student Dashboard

View approved and available events

Search events by title or location

Register for events (seat-limited)

Cancel registrations

Visual status indicators:

Open / Closed

Event Full

Email notification on successful registration

⚙️ Smart Event Logic

Automatic seat tracking

Prevents overbooking

Registration disabled when:

Event is manually closed

Maximum seats are reached

Toggle registration status instantly

🧰 Tech Stack
Layer	Technology
Backend	Flask (Python)
Database	MySQL
Frontend	HTML, CSS, Bootstrap
Authentication	Flask Sessions
Email Service	Flask-Mail
Data Export	CSV
Version Control	Git & GitHub
📂 Project Structure
event_portal/
│
├── app.py                 # App entry point
├── auth.py                # Routes & business logic
├── models.py              # Database models
├── extensions.py          # MySQL & Mail setup
├── config.py              # Configuration
│
├── templates/
│   ├── admin/             # Admin views
│   ├── organizer/         # Organizer views
│   └── student/           # Student views
│
├── static/
│   └── css/
│
├── .gitignore
└── README.md
🔐 Environment Setup

Create a .env file (not included in repo):

SECRET_KEY=your_secret_key
MYSQL_HOST=localhost
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_DB=event_portal
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
▶️ Run Locally
# Clone the repository
git clone https://github.com/Adhi1-2/college-event-management-system.git


# Navigate to project
cd event_portal


# Create virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows


# Install dependencies
pip install -r requirements.txt


# Run the app
python app.py

Access the app at:
👉 http://127.0.0.1:5050

📊 Key Highlights (Why This Project Stands Out)

✅ Real-world business logic
✅ Multi-role architecture
✅ Dynamic registration control
✅ Admin approval workflow
✅ CSV exports (organizer analytics)
✅ Email notifications
✅ Clean UI with Bootstrap
✅ Secure session handling

This is not a basic CRUD app — it models real production behavior.

📈 Future Enhancements

REST API version

React / Vue frontend

QR-based attendance system

Payment integration

Docker deployment

Cloud hosting

👨‍💻 Author

Adhinan S
Computer Science Student
Aspiring Full-Stack Developer

🔗 GitHub: https://github.com/Adhi1-2

⭐ Final Note

If you find this project useful or inspiring, feel free to star ⭐ the repository.

This project represents a strong foundation for scalable, real-world web applications.
