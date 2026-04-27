import sqlite3
import os

# DB_FILE = "attendance.db"
DB_FILE = os.path.join(os.path.dirname(__file__), 'attendance.db')


# Delete the old database file if it exists
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print("Old database removed.")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
print("Creating new database...")

# 1. Users Table (with 'role' and 'password')
# For this project, we'll store passwords as plain text for simplicity.
# In a real-world app, you MUST hash passwords.
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin')),
        password TEXT NOT NULL
    )
''')
print("Table 'users' created.")

# 2. Subjects Table (links a subject to a teacher)
cursor.execute('''
    CREATE TABLE subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        teacher_id TEXT NOT NULL,
        FOREIGN KEY (teacher_id) REFERENCES users (user_id)
    )
''')
print("Table 'subjects' created.")

# 3. Enrollments Table (links students to subjects)
cursor.execute('''
    CREATE TABLE enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        UNIQUE(student_id, subject_id),
        FOREIGN KEY (student_id) REFERENCES users (user_id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
''')
print("Table 'enrollments' created.")

# 4. Attendance Records Table (now includes subject_id)
cursor.execute('''
    CREATE TABLE attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT DEFAULT 'Present',
        FOREIGN KEY (student_id) REFERENCES users (user_id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
''')
print("Table 'attendance_records' created.")

# Create a default admin user for initial login
# Password is 'admin' for simplicity
try:
    cursor.execute(
        "INSERT INTO users (user_id, name, role, password) VALUES (?, ?, ?, ?)",
        ('admin', 'Administrator', 'admin', 'admin')
    )
    print("\nDefault admin user created with user_id 'admin' and password 'admin'.")
except sqlite3.IntegrityError:
    print("Admin user already exists.")


conn.commit()
conn.close()

print("\nNew database schema created successfully.")