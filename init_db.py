import sqlite3
import os
# DATABASE = 'attendance.db'
DATABASE = os.path.join(os.path.dirname(__file__), 'attendance.db')


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    # Create subjects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        teacher_id TEXT NOT NULL,
        FOREIGN KEY (teacher_id) REFERENCES users (user_id)
    )
    ''')

    # Create enrollments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enrollments (
        student_id TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        PRIMARY KEY (student_id, subject_id),
        FOREIGN KEY (student_id) REFERENCES users (user_id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
    ''')

    # Create attendance records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES users (user_id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
    ''')

    # Add a default admin user if none exists
    cursor.execute("SELECT * FROM users WHERE user_id = 'admin1'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (user_id, name, role, password)
            VALUES ('admin1', 'Admin User', 'admin', 'admin123')
        ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
