from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, StudentReport
import shutil
import os
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "static/student_reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
