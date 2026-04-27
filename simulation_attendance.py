import database_manager as db

def simulate():
    print("--- Attendance Simulation Tool ---")
    subjects = db.get_all_subjects()
    if not subjects:
        print("No subjects found. Please create subjects in the admin panel.")
        return

    print("Available Subjects:")
    for s in subjects:
        print(f"  - ID: {s['id']}, Name: {s['subject_name']}")
    
    try:
        subject_id = int(input("Enter the Subject ID for the session: "))
    except ValueError:
        print("Invalid ID.")
        return

    students = db.get_enrolled_students(subject_id)
    if not students:
        print("No students are enrolled in this subject.")
        return
        
    print("\nEnrolled Students:")
    for st in students:
        print(f"  - ID: {st['user_id']}, Name: {st['name']}")
    
    student_id = input("Enter the Student ID to mark as present: ")
    
    if student_id not in [s['user_id'] for s in students]:
        print("Error: This student is not enrolled in this subject.")
        return

    db.log_attendance(student_id, subject_id)
    print(f"\nAttendance logged for student {student_id} in subject {subject_id}.")

if __name__ == '__main__':
    simulate()