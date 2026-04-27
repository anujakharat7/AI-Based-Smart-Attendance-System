# import cv2
# from ai_modules import face_recognition as fr
# from ai_modules.liveness_detection import BlinkDetector
# import time
# from flask import Response
# from flask import Flask, render_template, request, redirect, url_for, session, flash
# import database_manager as db
# from datetime import datetime
# import calendar
# from functools import wraps

# app = Flask(__name__)
# app.secret_key = 'your_super_secret_key' 

# # --- Decorators & Auth ---
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session: return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

# def role_required(role_name):
#     def wrapper(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             if session.get('role') != role_name:
#                 flash("You do not have permission to access this page.", "danger")
#                 return redirect(url_for('dashboard'))
#             return f(*args, **kwargs)
#         return decorated_function
#     return wrapper

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user_id, password = request.form['user_id'], request.form['password']
#         user = db.validate_login(user_id, password)
#         if user:
#             session['user_id'], session['name'], session['role'] = user['user_id'], user['name'], user['role']
#             return redirect(url_for('dashboard'))
#         else:
#             flash("Invalid credentials, please try again.", "danger")
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))

# @app.route('/')
# @login_required
# def dashboard():
#     if session['role'] == 'admin':
#         stats = {'students': db.get_user_count_by_role('student'),'teachers': db.get_user_count_by_role('teacher'),'subjects': db.get_subject_count()}
#         return render_template('admin_dashboard.html', stats=stats)
#     elif session['role'] == 'teacher':
#         teacher_id = session['user_id']
#         # The database function now provides the student count directly, so no loop is needed here!
#         subjects = db.get_subjects_for_teacher(teacher_id)
        
#         stats = {
#             'subject_count': len(subjects),
#             'total_students': db.get_total_student_count_for_teacher(teacher_id)
#         }
#         return render_template('teacher_dashboard.html', subjects=subjects, stats=stats)
#     else:
#         return "Student Dashboard (Not Implemented Yet)"

# # --- Admin Routes ---
# @app.route('/admin/users')
# @login_required
# @role_required('admin')
# def manage_users():
#     return render_template('manage_users.html', users=db.get_all_users_by_role())

# @app.route('/admin/add_user', methods=['POST'])
# @login_required
# @role_required('admin')
# def add_user():
#     db.add_user(request.form['user_id'], request.form['name'], request.form['role'], request.form['password'])
#     flash(f"User '{request.form['name']}' added successfully!", "success")
#     return redirect(url_for('manage_users'))

# @app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def edit_user(user_id):
#     if request.method == 'POST':
#         db.update_user(user_id, request.form['name'], request.form['role'], request.form.get('password'))
#         flash(f"User '{request.form['name']}' updated successfully!", "success")
#         return redirect(url_for('manage_users'))
#     return render_template('edit_user.html', user=db.get_user_by_id(user_id))

# @app.route('/admin/subjects', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def manage_subjects():
#     if request.method == 'POST':
#         db.add_subject(request.form['subject_name'], request.form['teacher_id'])
#         flash(f"Subject '{request.form['subject_name']}' created successfully!", "success")
#         return redirect(url_for('manage_subjects'))
#     return render_template('manage_subjects.html', subjects=db.get_all_subjects(), teachers=db.get_all_users_by_role('teacher'))

# @app.route('/admin/enrollments', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def manage_enrollments():
#     selected_subject_id = request.args.get('subject_id', type=int)
#     enrolled_students = [s['user_id'] for s in db.get_enrolled_students(selected_subject_id)] if selected_subject_id else []
#     if request.method == 'POST':
#         subject_id = request.form.get('subject_id')
#         enrolled_ids = request.form.getlist('student_ids')
#         currently_enrolled = [s['user_id'] for s in db.get_enrolled_students(subject_id)]
#         for sid in enrolled_ids:
#             if sid not in currently_enrolled: db.enroll_student(sid, subject_id)
#         for sid in currently_enrolled:
#             if sid not in enrolled_ids: db.unenroll_student(sid, subject_id)
#         flash("Enrollments updated!", "success")
#         return redirect(url_for('manage_enrollments', subject_id=subject_id))
#     return render_template('manage_enrollments.html', subjects=db.get_all_subjects(), students=db.get_all_users_by_role('student'), 
#                            selected_subject_id=selected_subject_id, enrolled_students=enrolled_students)

# # --- Teacher Routes ---
# @app.route('/teacher/session/<int:subject_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('teacher')
# def attendance_session(subject_id):
#     if request.method == 'POST':
#         db.manual_attendance_update(request.form['student_id'], subject_id, request.form['status'])
#         flash(f"Marked {request.form['student_id']} as {request.form['status']}", "info")
#         return redirect(url_for('attendance_session', subject_id=subject_id))
#     subject = db.get_subject_by_id(subject_id)
#     enrolled_students = db.get_enrolled_students(subject_id)
#     attendance_status = {r['student_id']: r['status'] for r in db.get_attendance_for_subject_today(subject_id)}
#     return render_template('attendance_session.html', subject=subject, enrolled_students=enrolled_students, attendance_status=attendance_status)

# @app.route('/teacher/class_list/<int:subject_id>')
# @login_required
# @role_required('teacher')
# def view_class_list(subject_id):
#     return render_template('class_list.html', subject=db.get_subject_by_id(subject_id), students=db.get_enrolled_students(subject_id))

# @app.route('/teacher/session_report/<int:subject_id>')
# @login_required
# @role_required('teacher')
# def session_report(subject_id):
#     enrolled_students = db.get_enrolled_students(subject_id)
#     present_ids = {r['student_id'] for r in db.get_attendance_for_subject_today(subject_id) if r['status'] == 'Present'}
#     present_students = [s for s in enrolled_students if s['user_id'] in present_ids]
#     absent_students = [s for s in enrolled_students if s['user_id'] not in present_ids]
#     return render_template('session_report.html', subject=db.get_subject_by_id(subject_id), present_students=present_students, 
#                            absent_students=absent_students, report_date=datetime.now().strftime('%B %d, %Y'))

# @app.route('/teacher/history/<int:subject_id>/<student_id>')
# @login_required
# @role_required('teacher')
# def student_history(subject_id, student_id):
#     return render_template('student_history.html', subject=db.get_subject_by_id(subject_id), 
#                            student=db.get_user_by_id(student_id), history=db.get_student_attendance_history(student_id, subject_id))

# @app.route('/teacher/historical_report/<int:subject_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('teacher')
# def historical_report(subject_id):
#     subject = db.get_subject_by_id(subject_id)
#     report_data, report_title, present_count, absent_count = [], "", 0, 0
    
#     if request.method == 'POST':
#         report_type = request.form.get('report_type')
#         if report_type == 'daily':
#             report_date = request.form['report_date']
#             report_data = db.get_attendance_for_subject_by_date(subject_id, report_date)
#             report_title = f"Report for {datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %d, %Y')}"
#             for record in report_data:
#                 if record['status'] == 'Present': present_count += 1
#                 elif record['status'] == 'Absent': absent_count += 1
#         elif report_type == 'monthly':
#             month_str = request.form['report_month']
#             year, month = map(int, month_str.split('-'))
#             _, num_days = calendar.monthrange(year, month)
#             start_date, end_date = f"{year}-{month:02d}-01", f"{year}-{month:02d}-{num_days}"
#             report_data = db.get_attendance_for_subject_by_month(subject_id, start_date, end_date)
#             report_title = f"Report for {datetime(year, month, 1).strftime('%B %Y')}"

#     return render_template('historical_report.html', subject=subject, report_data=report_data,
#                            report_title=report_title, present_count=present_count, absent_count=absent_count)


# # Add this route to stream video and mark attendance
# @app.route('/video_feed/<int:subject_id>')
# @login_required
# @role_required('teacher')
# def video_feed(subject_id):
#     return Response(gen_frames(subject_id), mimetype='multipart/x-mixed-replace; boundary=frame')

# def gen_frames(subject_id):
#     """
#     Generator that yields MJPEG frames after marking attendance for matches.
#     """
#     cap = cv2.VideoCapture(0)  # default camera; change to rtsp/usb index as required
#     blink_detectors = {}  # per-person blink detector, keyed by user_id
#     recognized_recent = {} # avoid repeated logging: {user_id: last_timestamp}
#     MIN_LOG_INTERVAL = 30  # seconds between auto-logs for same user

#     try:
#         while True:
#             success, frame = cap.read()
#             if not success:
#                 break

#             # detect faces and try to recognize
#             matches = fr.recognize_faces_in_frame(frame, tolerance=0.5)
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#             for m in matches:
#                 user_id = m['user_id']
#                 top, right, bottom, left = m['location']
#                 # draw box + label
#                 cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
#                 cv2.putText(frame, f"{user_id} {m['distance']:.2f}", (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

#                 # liveness blink check
#                 if user_id not in blink_detectors:
#                     blink_detectors[user_id] = BlinkDetector()
#                 blinked = blink_detectors[user_id].process(gray, m['location'])

#                 now_ts = time.time()
#                 last = recognized_recent.get(user_id, 0)
#                 if blinked and (now_ts - last) > MIN_LOG_INTERVAL:
#                     # log attendance
#                     import database_manager as db
#                     db.log_attendance(user_id, subject_id, status='Present')
#                     recognized_recent[user_id] = now_ts
#                     # show mark text
#                     cv2.putText(frame, f"Marked {user_id}", (left, bottom+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

#             # encode frame as jpeg
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame_bytes = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
#     finally:
#         cap.release()

# if __name__ == '__main__':
#     app.run(debug=True)


# app.py (complete)------------NEW CODEGOES BELOW:
# import os
# import time
# from datetime import datetime
# from functools import wraps

# import cv2
# from flask import (Flask, Response, flash, redirect, render_template, request,
#                    session, url_for)
# from werkzeug.utils import secure_filename

# # import your DB helper
# import database_manager as db

# # import our AI modules (make sure these files exist)
# from ai_modules import face_recognition as fr
# from ai_modules.liveness_detection import BlinkDetector

# # --- Flask app setup ---
# app = Flask(__name__)
# app.secret_key = 'your_super_secret_key'  # replace in production

# # Where to store uploaded enrollment photos (use same folder fr expects if available)
# DATASET_DIR = getattr(fr, "DATA_DIR", os.path.join(os.path.dirname(__file__), "face_dataset"))
# ENCODINGS_FILE = getattr(fr, "ENCODINGS_FILE", os.path.join(os.path.dirname(__file__), "encodings", "encodings.pkl"))

# # Ensure dataset + encodings dir exist
# os.makedirs(DATASET_DIR, exist_ok=True)
# os.makedirs(os.path.dirname(ENCODINGS_FILE), exist_ok=True)


# # -------------------------
# # Authentication decorators
# # -------------------------
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'user_id' not in session:
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function

# def role_required(role_name):
#     def wrapper(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             if session.get('role') != role_name:
#                 flash("You do not have permission to access this page.", "danger")
#                 return redirect(url_for('dashboard'))
#             return f(*args, **kwargs)
#         return decorated_function
#     return wrapper


# # -------------------------
# # Auth & Dashboard routes
# # -------------------------
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user_id, password = request.form['user_id'], request.form['password']
#         user = db.validate_login(user_id, password)
#         if user:
#             session['user_id'], session['name'], session['role'] = user['user_id'], user['name'], user['role']
#             return redirect(url_for('dashboard'))
#         else:
#             flash("Invalid credentials, please try again.", "danger")
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))

# @app.route('/')
# @login_required
# def dashboard():
#     if session['role'] == 'admin':
#         stats = {'students': db.get_user_count_by_role('student'),
#                  'teachers': db.get_user_count_by_role('teacher'),
#                  'subjects': db.get_subject_count()}
#         return render_template('admin_dashboard.html', stats=stats)
#     elif session['role'] == 'teacher':
#         teacher_id = session['user_id']
#         subjects = db.get_subjects_for_teacher(teacher_id)
#         stats = {
#             'subject_count': len(subjects),
#             'total_students': db.get_total_student_count_for_teacher(teacher_id)
#         }
#         return render_template('teacher_dashboard.html', subjects=subjects, stats=stats)
#     else:
#         return "Student Dashboard (Not Implemented Yet)"


# # -------------------------
# # Admin routes (users/subjects/enrollments)
# # -------------------------
# @app.route('/admin/users')
# @login_required
# @role_required('admin')
# def manage_users():
#     return render_template('manage_users.html', users=db.get_all_users_by_role())

# @app.route('/admin/add_user', methods=['POST'])
# @login_required
# @role_required('admin')
# def add_user():
#     db.add_user(request.form['user_id'], request.form['name'], request.form['role'], request.form['password'])
#     flash(f"User '{request.form['name']}' added successfully!", "success")
#     return redirect(url_for('manage_users'))

# @app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def edit_user(user_id):
#     if request.method == 'POST':
#         db.update_user(user_id, request.form['name'], request.form['role'], request.form.get('password'))
#         flash(f"User '{request.form['name']}' updated successfully!", "success")
#         return redirect(url_for('manage_users'))
#     return render_template('edit_user.html', user=db.get_user_by_id(user_id))

# @app.route('/admin/subjects', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def manage_subjects():
#     if request.method == 'POST':
#         db.add_subject(request.form['subject_name'], request.form['teacher_id'])
#         flash(f"Subject '{request.form['subject_name']}' created successfully!", "success")
#         return redirect(url_for('manage_subjects'))
#     return render_template('manage_subjects.html', subjects=db.get_all_subjects(), teachers=db.get_all_users_by_role('teacher'))

# @app.route('/admin/enrollments', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def manage_enrollments():
#     selected_subject_id = request.args.get('subject_id', type=int)
#     enrolled_students = [s['user_id'] for s in db.get_enrolled_students(selected_subject_id)] if selected_subject_id else []
#     if request.method == 'POST':
#         subject_id = request.form.get('subject_id')
#         enrolled_ids = request.form.getlist('student_ids')
#         currently_enrolled = [s['user_id'] for s in db.get_enrolled_students(subject_id)]
#         for sid in enrolled_ids:
#             if sid not in currently_enrolled: db.enroll_student(sid, subject_id)
#         for sid in currently_enrolled:
#             if sid not in enrolled_ids: db.unenroll_student(sid, subject_id)
#         flash("Enrollments updated!", "success")
#         return redirect(url_for('manage_enrollments', subject_id=subject_id))
#     return render_template('manage_enrollments.html', subjects=db.get_all_subjects(), students=db.get_all_users_by_role('student'),
#                            selected_subject_id=selected_subject_id, enrolled_students=enrolled_students)


# # -------------------------
# # Enrollment (Option A) - Admin uploads multiple photos to enroll user
# # -------------------------
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/admin/enroll/<user_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def enroll_user(user_id):
#     """
#     Admin uploads multiple photos for a user; images stored under DATASET_DIR/<user_id>/
#     After upload, encodings are rebuilt by calling fr.build_encodings()
#     """
#     user_folder = os.path.join(DATASET_DIR, user_id)
#     os.makedirs(user_folder, exist_ok=True)

#     if request.method == 'POST':
#         if 'photos' not in request.files:
#             flash("No photos part in request.", "danger")
#             return redirect(request.url)
#         files = request.files.getlist('photos')
#         saved_any = False
#         for file in files:
#             if file and allowed_file(file.filename):
#                 filename = secure_filename(file.filename)
#                 save_path = os.path.join(user_folder, filename)
#                 file.save(save_path)
#                 saved_any = True
#         if not saved_any:
#             flash("No valid image files uploaded. Allowed: png, jpg, jpeg", "warning")
#             return redirect(request.url)

#         # Rebuild encodings (face_recognition module function)
#         try:
#             fr.build_encodings()
#             flash(f"Enrollment successful for user {user_id}. Encodings updated.", "success")
#         except Exception as e:
#             flash(f"Enrollment saved but failed to build encodings: {e}", "warning")

#         return redirect(url_for('manage_users'))

#     # GET: show simple upload page (create template at templates/enroll.html)
#     return render_template('enroll.html', user_id=user_id)


# # -------------------------
# # Teacher routes: attendance session / reports
# # -------------------------
# @app.route('/teacher/session/<int:subject_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('teacher')
# def attendance_session(subject_id):
#     if request.method == 'POST':
#         db.manual_attendance_update(request.form['student_id'], subject_id, request.form['status'])
#         flash(f"Marked {request.form['student_id']} as {request.form['status']}", "info")
#         return redirect(url_for('attendance_session', subject_id=subject_id))
#     subject = db.get_subject_by_id(subject_id)
#     enrolled_students = db.get_enrolled_students(subject_id)
#     attendance_status = {r['student_id']: r['status'] for r in db.get_attendance_for_subject_today(subject_id)}
#     return render_template('attendance_session.html', subject=subject, enrolled_students=enrolled_students, attendance_status=attendance_status)

# @app.route('/teacher/class_list/<int:subject_id>')
# @login_required
# @role_required('teacher')
# def view_class_list(subject_id):
#     return render_template('class_list.html', subject=db.get_subject_by_id(subject_id), students=db.get_enrolled_students(subject_id))

# @app.route('/teacher/session_report/<int:subject_id>')
# @login_required
# @role_required('teacher')
# def session_report(subject_id):
#     enrolled_students = db.get_enrolled_students(subject_id)
#     present_ids = {r['student_id'] for r in db.get_attendance_for_subject_today(subject_id) if r['status'] == 'Present'}
#     present_students = [s for s in enrolled_students if s['user_id'] in present_ids]
#     absent_students = [s for s in enrolled_students if s['user_id'] not in present_ids]
#     return render_template('session_report.html', subject=db.get_subject_by_id(subject_id), present_students=present_students,
#                            absent_students=absent_students, report_date=datetime.now().strftime('%B %d, %Y'))

# @app.route('/teacher/history/<int:subject_id>/<student_id>')
# @login_required
# @role_required('teacher')
# def student_history(subject_id, student_id):
#     return render_template('student_history.html', subject=db.get_subject_by_id(subject_id),
#                            student=db.get_user_by_id(student_id), history=db.get_student_attendance_history(student_id, subject_id))

# @app.route('/teacher/historical_report/<int:subject_id>', methods=['GET', 'POST'])
# @login_required
# @role_required('teacher')
# def historical_report(subject_id):
#     subject = db.get_subject_by_id(subject_id)
#     report_data, report_title, present_count, absent_count = [], "", 0, 0

#     if request.method == 'POST':
#         report_type = request.form.get('report_type')
#         if report_type == 'daily':
#             report_date = request.form['report_date']
#             report_data = db.get_attendance_for_subject_by_date(subject_id, report_date)
#             report_title = f"Report for {datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %d, %Y')}"
#             for record in report_data:
#                 if record['status'] == 'Present':
#                     present_count += 1
#                 elif record['status'] == 'Absent':
#                     absent_count += 1
#         elif report_type == 'monthly':
#             month_str = request.form['report_month']
#             year, month = map(int, month_str.split('-'))
#             _, num_days = __import__('calendar').monthrange(year, month)
#             start_date, end_date = f"{year}-{month:02d}-01", f"{year}-{month:02d}-{num_days}"
#             report_data = db.get_attendance_for_subject_by_month(subject_id, start_date, end_date)
#             report_title = f"Report for {datetime(year, month, 1).strftime('%B %Y')}"

#     return render_template('historical_report.html', subject=subject, report_data=report_data,
#                            report_title=report_title, present_count=present_count, absent_count=absent_count)


# # -------------------------
# # Attendance detection & video streaming
# # -------------------------
# @app.route('/video_feed/<int:subject_id>')
# @login_required
# @role_required('teacher')
# def video_feed(subject_id):
#     return Response(gen_frames(subject_id), mimetype='multipart/x-mixed-replace; boundary=frame')

# def mark_attendance_record(student_id, subject_id, status='Present'):
#     """
#     Try to use db.log_attendance if available; otherwise fall back to manual_attendance_update.
#     """
#     try:
#         # prefer log_attendance if defined
#         if hasattr(db, "log_attendance"):
#             db.log_attendance(student_id, subject_id, status=status)
#         else:
#             # fallback
#             db.manual_attendance_update(student_id, subject_id, status)
#     except Exception as e:
#         # Avoid failing the video stream; log to console
#         print("Failed to mark attendance:", e)

# def gen_frames(subject_id):
#     """
#     Generator that yields MJPEG frames after marking attendance for matches.
#     Uses fr.recognize_faces_in_frame(frame) which should return a list of dicts:
#       [{'user_id': 'abc', 'location': (top,right,bottom,left), 'distance': 0.42}, ...]
#     """
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("ERROR: Unable to open camera (index 0).")
#     blink_detectors = {}
#     recognized_recent = {}
#     MIN_LOG_INTERVAL = 30  # seconds to avoid duplicate logging for same user

#     try:
#         while True:
#             success, frame = cap.read()
#             if not success:
#                 break

#             # Recognize faces (fr.recognize_faces_in_frame uses face_recognition under the hood)
#             try:
#                 matches = fr.recognize_faces_in_frame(frame, tolerance=0.5)
#             except Exception as e:
#                 matches = []
#                 print("Face recognition error:", e)

#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#             for m in matches:
#                 user_id = m.get('user_id')
#                 top, right, bottom, left = m.get('location')
#                 # Draw rectangle and label
#                 cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
#                 label = f"{user_id} {m.get('distance', 0):.2f}"
#                 cv2.putText(frame, label, (left, max(10, top - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

#                 # Liveness check via blink
#                 if user_id not in blink_detectors:
#                     blink_detectors[user_id] = BlinkDetector()
#                 try:
#                     blinked = blink_detectors[user_id].process(gray, m['location'])
#                 except Exception:
#                     blinked = False

#                 now_ts = time.time()
#                 last_ts = recognized_recent.get(user_id, 0)
#                 if blinked and (now_ts - last_ts) > MIN_LOG_INTERVAL:
#                     # Mark attendance in DB
#                     mark_attendance_record(user_id, subject_id, status='Present')
#                     recognized_recent[user_id] = now_ts
#                     # Visual feedback
#                     cv2.putText(frame, f"Marked {user_id}", (left, bottom + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

#             # Encode and stream frame
#             ret, buffer = cv2.imencode('.jpg', frame)
#             if not ret:
#                 continue
#             frame_bytes = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
#     finally:
#         cap.release()


# # -------------------------
# # Run
# # -------------------------
# if __name__ == '__main__':
#     app.run(debug=True)



#NEW CODE ALONG WITH WEBCAM CAPTURE SUPPORT :
import os
import time
import base64
from datetime import datetime
from functools import wraps

import cv2
from flask import (Flask, Response, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.utils import secure_filename

# import your DB helper
import database_manager as db

# import our AI modules (make sure these files exist)
from ai_modules import face_recognition as fr
from ai_modules.liveness_detection import BlinkDetector

# --- Flask app setup ---
app = Flask(__name__)
app.secret_key = 'your_super_secret_key'  # replace in production

# Where to store uploaded enrollment photos
DATASET_DIR = getattr(fr, "DATA_DIR", os.path.join(os.path.dirname(__file__), "face_dataset"))
ENCODINGS_FILE = getattr(fr, "ENCODINGS_FILE", os.path.join(os.path.dirname(__file__), "encodings", "encodings.pkl"))

# Ensure dataset + encodings dir exist
os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ENCODINGS_FILE), exist_ok=True)


# -------------------------
# Authentication decorators
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role_name:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper


# -------------------------
# Auth & Dashboard routes
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id, password = request.form['user_id'], request.form['password']
        user = db.validate_login(user_id, password)
        if user:
            session['user_id'], session['name'], session['role'] = user['user_id'], user['name'], user['role']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials, please try again.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    if session['role'] == 'admin':
        stats = {'students': db.get_user_count_by_role('student'),
                 'teachers': db.get_user_count_by_role('teacher'),
                 'subjects': db.get_subject_count()}
        return render_template('admin_dashboard.html', stats=stats)
    elif session['role'] == 'teacher':
        teacher_id = session['user_id']
        subjects = db.get_subjects_for_teacher(teacher_id)
        stats = {
            'subject_count': len(subjects),
            'total_students': db.get_total_student_count_for_teacher(teacher_id)
        }
        return render_template('teacher_dashboard.html', subjects=subjects, stats=stats)
    else:
        return "Student Dashboard (Not Implemented Yet)"


# -------------------------
# Admin routes (users/subjects/enrollments)
# -------------------------
@app.route('/admin/users')
@login_required
@role_required('admin')
def manage_users():
    return render_template('manage_users.html', users=db.get_all_users_by_role())

@app.route('/admin/add_user', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    db.add_user(request.form['user_id'], request.form['name'], request.form['role'], request.form['password'])
    flash(f"User '{request.form['name']}' added successfully!", "success")
    return redirect(url_for('manage_users'))

@app.route('/admin/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    if request.method == 'POST':
        db.update_user(user_id, request.form['name'], request.form['role'], request.form.get('password'))
        flash(f"User '{request.form['name']}' updated successfully!", "success")
        return redirect(url_for('manage_users'))
    return render_template('edit_user.html', user=db.get_user_by_id(user_id))

@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_subjects():
    if request.method == 'POST':
        db.add_subject(request.form['subject_name'], request.form['teacher_id'])
        flash(f"Subject '{request.form['subject_name']}' created successfully!", "success")
        return redirect(url_for('manage_subjects'))
    return render_template('manage_subjects.html', subjects=db.get_all_subjects(), teachers=db.get_all_users_by_role('teacher'))

@app.route('/admin/enrollments', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_enrollments():
    selected_subject_id = request.args.get('subject_id', type=int)
    enrolled_students = [s['user_id'] for s in db.get_enrolled_students(selected_subject_id)] if selected_subject_id else []
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        enrolled_ids = request.form.getlist('student_ids')
        currently_enrolled = [s['user_id'] for s in db.get_enrolled_students(subject_id)]
        for sid in enrolled_ids:
            if sid not in currently_enrolled: db.enroll_student(sid, subject_id)
        for sid in currently_enrolled:
            if sid not in enrolled_ids: db.unenroll_student(sid, subject_id)
        flash("Enrollments updated!", "success")
        return redirect(url_for('manage_enrollments', subject_id=subject_id))
    return render_template('manage_enrollments.html', subjects=db.get_all_subjects(), students=db.get_all_users_by_role('student'),
                           selected_subject_id=selected_subject_id, enrolled_students=enrolled_students)


# -------------------------
# Enrollment (Upload + Webcam)
# -------------------------
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/enroll/<user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def enroll_user(user_id):
    """
    Admin enrolls a user by either uploading photos OR capturing via webcam.
    - Upload field name: 'photos' (multiple)
    - Webcam capture field (base64): 'captured_image'
    """
    user_folder = os.path.join(DATASET_DIR, user_id)
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        saved_any = False

        # A) file uploads
        if 'photos' in request.files:
            files = request.files.getlist('photos')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(user_folder, filename)
                    file.save(save_path)
                    saved_any = True

        # B) single base64 capture
        b64 = request.form.get('captured_image')
        if b64:
            try:
                if ',' in b64:
                    b64 = b64.split(',', 1)[1]
                img_bytes = base64.b64decode(b64)
                ts = int(time.time())
                save_path = os.path.join(user_folder, f"capture_{ts}.png")
                with open(save_path, "wb") as f:
                    f.write(img_bytes)
                saved_any = True
            except Exception as e:
                flash(f"Failed to save captured image: {e}", "danger")

        if not saved_any:
            flash("No valid images provided. Allowed: png, jpg, jpeg", "warning")
            return redirect(request.url)

        # rebuild encodings
        try:
            num_users, num_imgs = fr.build_encodings()
            flash(f"Enrollment updated. (users: {num_users}, images encoded: {num_imgs})", "success")
        except Exception as e:
            flash(f"Enrollment saved but encodings rebuild failed: {e}", "warning")

        return redirect(url_for('manage_users'))

    return render_template('enroll.html', user_id=user_id)


# -------------------------
# Teacher routes
# -------------------------
@app.route('/teacher/session/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def attendance_session(subject_id):
    if request.method == 'POST':
        db.manual_attendance_update(request.form['student_id'], subject_id, request.form['status'])
        flash(f"Marked {request.form['student_id']} as {request.form['status']}", "info")
        return redirect(url_for('attendance_session', subject_id=subject_id))
    subject = db.get_subject_by_id(subject_id)
    enrolled_students = db.get_enrolled_students(subject_id)
    attendance_status = {r['student_id']: r['status'] for r in db.get_attendance_for_subject_today(subject_id)}
    return render_template('attendance_session.html', subject=subject, enrolled_students=enrolled_students, attendance_status=attendance_status)

@app.route('/teacher/class_list/<int:subject_id>')
@login_required
@role_required('teacher')
def view_class_list(subject_id):
    return render_template('class_list.html', subject=db.get_subject_by_id(subject_id), students=db.get_enrolled_students(subject_id))

@app.route('/teacher/session_report/<int:subject_id>')
@login_required
@role_required('teacher')
def session_report(subject_id):
    enrolled_students = db.get_enrolled_students(subject_id)
    present_ids = {r['student_id'] for r in db.get_attendance_for_subject_today(subject_id) if r['status'] == 'Present'}
    present_students = [s for s in enrolled_students if s['user_id'] in present_ids]
    absent_students = [s for s in enrolled_students if s['user_id'] not in present_ids]
    return render_template('session_report.html', subject=db.get_subject_by_id(subject_id), present_students=present_students,
                           absent_students=absent_students, report_date=datetime.now().strftime('%B %d, %Y'))

@app.route('/teacher/history/<int:subject_id>/<student_id>')
@login_required
@role_required('teacher')
def student_history(subject_id, student_id):
    return render_template('student_history.html', subject=db.get_subject_by_id(subject_id),
                           student=db.get_user_by_id(student_id), history=db.get_student_attendance_history(student_id, subject_id))

@app.route('/teacher/historical_report/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def historical_report(subject_id):
    subject = db.get_subject_by_id(subject_id)
    report_data, report_title, present_count, absent_count = [], "", 0, 0

    if request.method == 'POST':
        report_type = request.form.get('report_type')
        if report_type == 'daily':
            report_date = request.form['report_date']
            report_data = db.get_attendance_for_subject_by_date(subject_id, report_date)
            report_title = f"Report for {datetime.strptime(report_date, '%Y-%m-%d').strftime('%B %d, %Y')}"
            for record in report_data:
                if record['status'] == 'Present':
                    present_count += 1
                elif record['status'] == 'Absent':
                    absent_count += 1
        elif report_type == 'monthly':
            month_str = request.form['report_month']
            year, month = map(int, month_str.split('-'))
            _, num_days = __import__('calendar').monthrange(year, month)
            start_date, end_date = f"{year}-{month:02d}-01", f"{year}-{month:02d}-{num_days}"
            report_data = db.get_attendance_for_subject_by_month(subject_id, start_date, end_date)
            report_title = f"Report for {datetime(year, month, 1).strftime('%B %Y')}"

    return render_template('historical_report.html', subject=subject, report_data=report_data,
                           report_title=report_title, present_count=present_count, absent_count=absent_count)


# -------------------------
# Attendance detection & video streaming
# -------------------------
@app.route('/video_feed/<int:subject_id>')
@login_required
@role_required('teacher')
def video_feed(subject_id):
    return Response(gen_frames(subject_id), mimetype='multipart/x-mixed-replace; boundary=frame')

def mark_attendance_record(student_id, subject_id, status='Present'):
    try:
        if hasattr(db, "log_attendance"):
            db.log_attendance(student_id, subject_id, status=status)
        else:
            db.manual_attendance_update(student_id, subject_id, status)
    except Exception as e:
        print("Failed to mark attendance:", e)

#new gen frames function with live detection:
def gen_frames(subject_id):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Unable to open camera (index 0).")
    blink_detectors = {}
    recognized_recent = {}
    MIN_LOG_INTERVAL = 30  # seconds between duplicate logs

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            try:
                matches = fr.recognize_faces_in_frame(frame, tolerance=0.5)
            except Exception as e:
                matches = []
                print("Face recognition error:", e)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            for m in matches:
                user_id = m.get('user_id')
                top, right, bottom, left = m.get('location')

                # Draw rectangle around detected face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                label = f"{user_id} {m.get('distance', 0):.2f}"
                cv2.putText(frame, label, (left, max(10, top - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Initialize blink detector for the user
                if user_id not in blink_detectors:
                    blink_detectors[user_id] = BlinkDetector()

                # Debugging for blink detection
                try:
                    blinked = blink_detectors[user_id].process(gray, m['location'])
                    print(f"Blink status for {user_id}: {blinked}")
                except Exception as e:
                    print("Blink detection error:", e)
                    blinked = False

                now_ts = time.time()
                last_ts = recognized_recent.get(user_id, 0)

                # --- TEMPORARY BYPASS: Ignore blink detection for testing ---
                # if (now_ts - last_ts) > MIN_LOG_INTERVAL:
                if blinked and (now_ts - last_ts) > MIN_LOG_INTERVAL:

                    print(f"Marking attendance for {user_id} in subject {subject_id}")
                    mark_attendance_record(user_id, subject_id, status='Present')
                    recognized_recent[user_id] = now_ts
                    cv2.putText(frame, f"Marked {user_id}", (left, bottom + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Stream frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()



# -------------------------
# Run
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)


