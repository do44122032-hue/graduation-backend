import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Course, Enrollment

def seed_courses():
    db = SessionLocal()
    try:
        # 1. Get a student (e.g., student.a@cihanuniversity.edu.iq)
        student = db.query(User).filter(User.role == "student").first()
        if not student:
            print("No student found. Please run seed_students.py first.")
            return

        print(f"DEBUG: Found student {student.name} (ID: {student.id})")

        # 2. Create some courses if they don't exist
        existing_courses = db.query(Course).all()
        if not existing_courses:
            courses = [
                Course(title="Clinical Medicine III", instructor="Dr. Sarah Williams", color_hex="CBD77E", icon_name="monitor_heart"),
                Course(title="Surgical Techniques", instructor="Dr. James Wilson", color_hex="E8C998", icon_name="medical_services"),
                Course(title="Medical Ethics", instructor="Dr. Emily Rodriguez", color_hex="82C4E6", icon_name="gavel"),
                Course(title="Clinical Pathology", instructor="Dr. Michael Chen", color_hex="FFB74D", icon_name="science"),
                Course(title="Pharmacology", instructor="Dr. Lisa Chang", color_hex="B39DDB", icon_name="medication"),
            ]
            db.add_all(courses)
            db.commit()
            for c in courses: db.refresh(c)
            existing_courses = courses
            print(f"Created {len(courses)} courses.")
        else:
            print(f"Found {len(existing_courses)} existing courses.")

        # 3. Enroll the student if not already enrolled
        for i, course in enumerate(existing_courses):
            existing_enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == student.id,
                Enrollment.course_id == course.id
            ).first()
            if not existing_enrollment:
                # Mock some progress/grades values based on the sample data in my_courses.dart
                progress_values = [0.75, 0.45, 0.90, 0.30, 0.60]
                grade_values = ["A-", "B+", "A", "Pending", "B"]
                next_class_values = ["Mon, 9:00 AM", "Tue, 2:00 PM", "Completed", "Thu, 10:00 AM", "Fri, 9:00 AM"]
                
                idx = i % len(progress_values)
                
                enr = Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    progress=progress_values[idx],
                    grade=grade_values[idx],
                    next_class=next_class_values[idx]
                )
                db.add(enr)
                print(f"Enrolled in {course.title}")
        
        db.commit()
        print(f"Successfully seeded courses for {student.name}")

    except Exception as e:
        print(f"Error seeding courses: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_courses()
