import sqlite3
from datetime import datetime
import os

# DATABASE = 'attendance.db'
DATABASE = os.path.join(os.path.dirname(__file__), 'attendance.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- User Management ---
def validate_login(user_id, password):
    conn = get_db_connection()
    user = conn.cursor().execute("SELECT * FROM users WHERE user_id = ? AND password = ?", (user_id, password)).fetchone()
    conn.close()
    return user

def add_user(user_id, name, role, password):
    conn = get_db_connection()
    try:
        conn.cursor().execute("INSERT INTO users (user_id, name, role, password) VALUES (?, ?, ?, ?)", (user_id, name, role, password))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def update_user(original_user_id, name, role, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    if password:
        cursor.execute("UPDATE users SET name = ?, role = ?, password = ? WHERE user_id = ?", (name, role, password, original_user_id))
    else:
        cursor.execute("UPDATE users SET name = ?, role = ? WHERE user_id = ?", (name, role, original_user_id))
    conn.commit()
    conn.close()

def get_all_users_by_role(role=None):
    conn = get_db_connection()
    query, params = "SELECT * FROM users", []
    if role:
        query += " WHERE role = ?"
        params.append(role)
    query += " ORDER BY name"
    users = conn.cursor().execute(query, params).fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.cursor().execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def get_user_count_by_role(role):
    conn = get_db_connection()
    count = conn.cursor().execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,)).fetchone()[0]
    conn.close()
    return count

# --- Subject & Enrollment Management ---
def add_subject(subject_name, teacher_id):
    conn = get_db_connection()
    conn.cursor().execute("INSERT INTO subjects (subject_name, teacher_id) VALUES (?, ?)", (subject_name, teacher_id))
    conn.commit()
    conn.close()

def get_all_subjects():
    conn = get_db_connection()
    subjects = conn.cursor().execute("SELECT s.id, s.subject_name, u.name as teacher_name FROM subjects s JOIN users u ON s.teacher_id = u.user_id").fetchall()
    conn.close()
    return subjects

def get_subject_count():
    conn = get_db_connection()
    count = conn.cursor().execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    conn.close()
    return count

def enroll_student(student_id, subject_id):
    conn = get_db_connection()
    try:
        conn.cursor().execute("INSERT INTO enrollments (student_id, subject_id) VALUES (?, ?)", (student_id, subject_id))
        conn.commit()
    except sqlite3.IntegrityError: pass
    finally: conn.close()

def unenroll_student(student_id, subject_id):
    conn = get_db_connection()
    conn.cursor().execute("DELETE FROM enrollments WHERE student_id = ? AND subject_id = ?", (student_id, subject_id))
    conn.commit()
    conn.close()
    
def get_enrolled_students(subject_id):
    conn = get_db_connection()
    students = conn.cursor().execute("SELECT u.* FROM users u JOIN enrollments e ON u.user_id = e.student_id WHERE e.subject_id = ?", (subject_id,)).fetchall()
    conn.close()
    return students

def get_subject_by_id(subject_id):
    conn = get_db_connection()
    subject = conn.cursor().execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    conn.close()
    return subject

# --- Teacher-Specific Functions ---
# **** THIS IS THE CORRECTED FUNCTION ****
def get_subjects_for_teacher(teacher_id):
    """
    Retrieves all subjects for a teacher AND includes the count of enrolled students
    for each subject using a single, efficient SQL query.
    """
    conn = get_db_connection()
    query = """
    SELECT s.id, s.subject_name, COUNT(e.student_id) as student_count
    FROM subjects s
    LEFT JOIN enrollments e ON s.id = e.subject_id
    WHERE s.teacher_id = ?
    GROUP BY s.id
    ORDER BY s.subject_name
    """
    subjects = conn.cursor().execute(query, (teacher_id,)).fetchall()
    conn.close()
    return subjects

def get_total_student_count_for_teacher(teacher_id):
    conn = get_db_connection()
    count = conn.cursor().execute("""
        SELECT COUNT(DISTINCT e.student_id) 
        FROM enrollments e 
        JOIN subjects s ON e.subject_id = s.id 
        WHERE s.teacher_id = ?
    """, (teacher_id,)).fetchone()[0]
    conn.close()
    return count

# --- Attendance Logging and Reporting ---
def manual_attendance_update(student_id, subject_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_date, timestamp = datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    existing_record = cursor.execute("SELECT id FROM attendance_records WHERE student_id = ? AND subject_id = ? AND date = ?", (student_id, subject_id, today_date)).fetchone()
    if existing_record:
        cursor.execute("UPDATE attendance_records SET status = ?, timestamp = ? WHERE id = ?", (status, timestamp, existing_record['id']))
    else:
        cursor.execute("INSERT INTO attendance_records (student_id, subject_id, timestamp, date, status) VALUES (?, ?, ?, ?, ?)", (student_id, subject_id, timestamp, today_date, status))
    conn.commit()
    conn.close()
#new fuction is below rest code is old code:
def log_attendance(student_id, subject_id, status='Present'):
    """
    Convenience function to mark attendance for now (same logic as manual_attendance_update but callable from recognition)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    today_date = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    existing = cursor.execute("SELECT id FROM attendance_records WHERE student_id = ? AND subject_id = ? AND date = ?",
                              (student_id, subject_id, today_date)).fetchone()
    if existing:
        cursor.execute("UPDATE attendance_records SET status = ?, timestamp = ? WHERE id = ?", (status, timestamp, existing['id']))
    else:
        cursor.execute("INSERT INTO attendance_records (student_id, subject_id, timestamp, date, status) VALUES (?, ?, ?, ?, ?)",
                       (student_id, subject_id, timestamp, today_date, status))
    conn.commit()
    conn.close()


def get_attendance_for_subject_today(subject_id):
    conn = get_db_connection()
    today_date = datetime.now().strftime('%Y-%m-%d')
    records = conn.cursor().execute("SELECT u.name, ar.student_id, ar.timestamp, ar.status FROM attendance_records ar JOIN users u ON ar.student_id = u.user_id WHERE ar.subject_id = ? AND ar.date = ? ORDER BY u.name", (subject_id, today_date)).fetchall()
    conn.close()
    return records

def get_attendance_for_subject_by_date(subject_id, report_date):
    conn = get_db_connection()
    records = conn.cursor().execute("SELECT u.name, ar.student_id, ar.timestamp, ar.status FROM attendance_records ar JOIN users u ON ar.student_id = u.user_id WHERE ar.subject_id = ? AND ar.date = ? ORDER BY u.name", (subject_id, report_date)).fetchall()
    conn.close()
    return records
    
def get_attendance_for_subject_by_month(subject_id, start_date, end_date):
    conn = get_db_connection()
    records = conn.cursor().execute("""
        SELECT u.name, ar.date, ar.timestamp, ar.status
        FROM attendance_records ar JOIN users u ON ar.student_id = u.user_id
        WHERE ar.subject_id = ? AND ar.date BETWEEN ? AND ?
        ORDER BY ar.date, u.name
    """, (subject_id, start_date, end_date)).fetchall()
    conn.close()
    return records

def get_student_attendance_history(student_id, subject_id):
    conn = get_db_connection()
    history = conn.cursor().execute("SELECT date, status, timestamp FROM attendance_records WHERE student_id = ? AND subject_id = ? ORDER BY date DESC", (student_id, subject_id)).fetchall()
    conn.close()
    return history