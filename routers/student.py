from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import User, StudentReport, StudentTask, Course, Enrollment
import shutil
import os
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "static/student_reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class TaskCreate(BaseModel):
    student_id: Optional[int] = None
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = ""
    color_hex: Optional[str] = "E8C998"


@router.post("/upload-report")
async def upload_student_report(
    uid: str = Form(...),
    doctor_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Student report upload request for user {uid} to doctor {doctor_id}")
    # 1. Verify Student
    student = None
    if uid.isdigit():
        student = db.query(User).filter(User.id == int(uid)).first()
    
    if not student:
        student = db.query(User).filter(User.uid == uid).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID/UID '{uid}' not found")

    # 2. Save File if present
    file_url = None
    if file:
        file_name = f"{student.id}_{datetime.now().timestamp()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_url = f"/static/student_reports/{file_name}"

    # 3. Save to Database
    try:
        new_report = StudentReport(
            student_id=student.id,
            doctor_id=doctor_id,
            title=title,
            description=description,
            file_url=file_url,
            status="submitted",
            submitted_at=datetime.now().isoformat()
        )
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Database error while saving report. Error: {str(e)}")

    return {"success": True, "data": new_report.to_dict()}


@router.get("/{uid}/reports")
async def get_student_reports(
    uid: str,
    db: Session = Depends(get_db)
):
    # Retrieve reports submitted by the student
    student = None
    if uid.isdigit():
        student = db.query(User).filter(User.id == int(uid)).first()
    
    if not student:
        student = db.query(User).filter(User.uid == uid).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID/UID '{uid}' not found")

    reports = db.query(StudentReport).filter(StudentReport.student_id == student.id).order_by(StudentReport.id.desc()).all()
    # To include doctor name it might be useful, let's just return basic dict
    return [r.to_dict() for r in reports]


@router.get("/doctor/{uid}/reports")
async def get_doctor_reports(
    uid: str,
    db: Session = Depends(get_db)
):
    # Retrieve reports submitted to this doctor
    doctor = None
    if uid.isdigit():
        doctor = db.query(User).filter(User.id == int(uid)).first()
    
    if not doctor:
        doctor = db.query(User).filter(User.uid == uid).first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with ID/UID '{uid}' not found")

    reports = db.query(StudentReport).filter(StudentReport.doctor_id == doctor.id).order_by(StudentReport.id.desc()).all()
    
    # Let's attach student name as well for the doctor to see
    result = []
    for r in reports:
        report_data = r.to_dict()
        st = db.query(User).filter(User.id == r.student_id).first()
        if st:
            report_data['studentName'] = st.name
        result.append(report_data)
    
    return result


# ─── Tasks ───────────────────────────────────────────────────────────

@router.get("/tasks/{uid}")
async def get_student_tasks(
    uid: str,
    db: Session = Depends(get_db)
):
    student = None
    if uid.isdigit():
        student = db.query(User).filter(User.id == int(uid)).first()
    
    if not student:
        student = db.query(User).filter(User.uid == uid).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID/UID '{uid}' not found")

    # Fetch tasks assigned to this student OR global tasks (student_id is null)
    tasks = db.query(StudentTask).filter(
        (StudentTask.student_id == student.id) | (StudentTask.student_id == None)
    ).all()
    
    return [t.to_dict() for t in tasks]

@router.post("/tasks")
async def create_student_task(
    title: str = Form(...),
    description: Optional[str] = Form(""),
    due_date: Optional[str] = Form(""),
    color_hex: Optional[str] = Form("E8C998"),
    student_id: Optional[int] = Form(None),
    doctor_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    print(f"DEBUG: create_student_task received - title: {title}, student_id: {student_id}, doctor_id: {doctor_id}")
    file_url = None
    if file:
        file_name = f"task_doc_{datetime.now().timestamp()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        print(f"DEBUG: Saving task file to {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_url = f"/static/student_reports/{file_name}"

    try:
        new_task = StudentTask(
            student_id=student_id,
            doctor_id=doctor_id,
            title=title,
            description=description,
            due_date=due_date,
            color_hex=color_hex,
            file_url=file_url,
            status="pending"
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        print(f"DEBUG: Successfully created task {new_task.id}")
        return {"success": True, "task": new_task.to_dict()}
    except Exception as e:
        db.rollback()
        print(f"ERROR creating task: {e}")
        return {"success": False, "detail": str(e)}

@router.post("/tasks/{task_id}/complete")
async def complete_student_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(StudentTask).filter(StudentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = "completed"
    db.commit()
    db.refresh(task)
    return {"success": True, "task": task.to_dict()}

@router.get("/doctor/{uid}/tasks")
async def get_doctor_assigned_tasks(
    uid: str,
    db: Session = Depends(get_db)
):
    doctor = None
    if uid.isdigit():
        doctor = db.query(User).filter(User.id == int(uid)).first()
    if not doctor:
        doctor = db.query(User).filter(User.uid == uid).first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    tasks = db.query(StudentTask).filter(StudentTask.doctor_id == doctor.id).all()
    
    # Let's attach student name
    result = []
    for t in tasks:
        t_dict = t.to_dict()
        if t.student_id:
            st = db.query(User).filter(User.id == t.student_id).first()
            if st:
                t_dict['studentName'] = st.name
        result.append(t_dict)
    
    return result

@router.get("/{uid}/courses")
async def get_student_courses(
    uid: str,
    db: Session = Depends(get_db)
):
    student = None
    if uid.isdigit():
        student = db.query(User).filter(User.id == int(uid)).first()
    
    if not student:
        student = db.query(User).filter(User.uid == uid).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID/UID '{uid}' not found")

    enrollments = db.query(Enrollment).filter(Enrollment.student_id == student.id).all()
    
    result = []
    for enr in enrollments:
        course = db.query(Course).filter(Course.id == enr.course_id).first()
        if course:
            c_dict = course.to_dict()
            e_dict = enr.to_dict()
            # Combine
            c_dict.update({
                "progress": e_dict["progress"],
                "grade": e_dict["grade"],
                "nextClass": e_dict["nextClass"]
            })
            result.append(c_dict)
    
    return result

@router.get("/courses/available/{uid}")
async def get_available_courses(
    uid: str,
    db: Session = Depends(get_db)
):
    student = None
    if uid.isdigit():
        student = db.query(User).filter(User.id == int(uid)).first()
    
    if not student:
        student = db.query(User).filter(User.uid == uid).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID/UID '{uid}' not found")

    # Get IDs of courses student is already in
    enrolled_course_ids = [e[0] for e in db.query(Enrollment.course_id).filter(Enrollment.student_id == student.id).all()]
    
    # Get all courses NOT in that list
    if not enrolled_course_ids:
        available_courses = db.query(Course).all()
    else:
        available_courses = db.query(Course).filter(~Course.id.in_(enrolled_course_ids)).all()
    
    return [c.to_dict() for c in available_courses]

@router.post("/enroll")
async def enroll_in_course(
    uid: str = Form(...),
    course_id: int = Form(...),
    db: Session = Depends(get_db)
):
    student = None
    if uid.isdigit():
        student = db.query(User).filter(User.id == int(uid)).first()
    
    if not student:
        student = db.query(User).filter(User.uid == uid).first()
    
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID/UID '{uid}' not found")

    # Check if already enrolled
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.course_id == course_id
    ).first()
    
    if existing:
        return {"success": False, "message": "Already enrolled in this course"}

    # Create enrollment
    new_enrollment = Enrollment(
        student_id=student.id,
        course_id=course_id,
        progress=0.0,
        grade="Pending",
        next_class="TBA"
    )
    
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return {"success": True, "enrollment": new_enrollment.to_dict()}

@router.post("/courses/seed")
async def seed_courses_api(db: Session = Depends(get_db)):
    # List of sample courses to ensure existence
    sample_courses = [
        {"title": "Clinical Medicine III", "instructor": "Dr. Sarah Williams", "color_hex": "CBD77E", "icon_name": "monitor_heart"},
        {"title": "Surgical Techniques", "instructor": "Dr. James Wilson", "color_hex": "E8C998", "icon_name": "medical_services"},
        {"title": "Medical Ethics", "instructor": "Dr. Emily Rodriguez", "color_hex": "82C4E6", "icon_name": "gavel"},
        {"title": "Clinical Pathology", "instructor": "Dr. Michael Chen", "color_hex": "FFB74D", "icon_name": "science"},
        {"title": "Pharmacology", "instructor": "Dr. Lisa Chang", "color_hex": "B39DDB", "icon_name": "medication"},
    ]
    
    added_count = 0
    for sc in sample_courses:
        # Check if course with this title already exists
        exists = db.query(Course).filter(Course.title == sc["title"]).first()
        if not exists:
            new_course = Course(
                title=sc["title"],
                instructor=sc["instructor"],
                color_hex=sc["color_hex"],
                icon_name=sc["icon_name"]
            )
            db.add(new_course)
            added_count = added_count + 1
    
    if added_count > 0:
        db.commit()
        return {"success": True, "message": f"Added {added_count} new courses"}
    
    return {"success": False, "message": "All sample courses already exist"}
