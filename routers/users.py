from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import User, DoctorSchedule

router = APIRouter()

# ─── Request Models ───────────────────────────────────────────────────────

class PatientProfileUpdate(BaseModel):
    uid: str  # Note: uid matches id in our schema for this project
    age: Optional[str] = None
    bloodType: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    dateOfBirth: Optional[str] = None
    socialStatus: Optional[str] = None
    chronicConditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None

class ScheduleCreate(BaseModel):
    day: str
    startTime: str
    endTime: str


# ─── Endpoints ───────────────────────────────────────────────────────────

@router.get("/profile/{uid}")
async def get_profile(uid: str, db: Session = Depends(get_db)):
    # Try ID first (most common), then original UID
    user = db.query(User).filter(User.id == int(uid) if uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == uid).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.get("/patients")
async def get_patients(db: Session = Depends(get_db)):
    """Fetch all users with the role 'patient'"""
    patients = db.query(User).filter(User.role == "patient").all()
    return [patient.to_dict() for patient in patients]


@router.get("/doctors")
async def get_doctors(db: Session = Depends(get_db)):
    """Fetch all users with the role 'doctor'"""
    doctors = db.query(User).filter(User.role == "doctor").all()
    return [doctor.to_dict() for doctor in doctors]


@router.get("/doctors/active")
async def get_active_doctors(db: Session = Depends(get_db)):
    """Fetch all ACTIVE users with the role 'doctor'"""
    doctors = db.query(User).filter(User.role == "doctor", User.is_active == True).all()
    return [doctor.to_dict() for doctor in doctors]


@router.get("/doctors/{uid}/schedule")
async def get_doctor_schedule(uid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(uid) if uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == uid).first()
    if not user or user.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    schedules = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == user.id).all()
    return [s.to_dict() for s in schedules]


@router.post("/doctors/{uid}/schedule")
async def add_doctor_schedule(uid: str, data: ScheduleCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(uid) if uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == uid).first()
    if not user or user.role != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    new_slot = DoctorSchedule(
        doctor_id=user.id,
        day=data.day,
        start_time=data.startTime,
        end_time=data.endTime,
        is_booked=False
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    
    return {"success": True, "schedule": new_slot.to_dict()}


@router.put("/patient-profile")
async def update_patient_profile(data: PatientProfileUpdate, db: Session = Depends(get_db)):
    # Lookup user
    user = db.query(User).filter(User.id == int(data.uid) if data.uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == data.uid).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if data.age: user.age = data.age
    if data.bloodType: user.blood_type = data.bloodType
    if data.height: user.height = data.height
    if data.weight: user.weight = data.weight
    if data.dateOfBirth: user.dob = data.dateOfBirth
    if data.socialStatus: user.social_status = data.socialStatus
    if data.chronicConditions is not None: user.chronic_conditions = data.chronicConditions
    if data.medications is not None: user.medications = data.medications
    
    db.commit()
    db.refresh(user)
    
    return {"success": True, "message": "Profile updated", "user": user.to_dict()}
