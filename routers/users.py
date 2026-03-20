from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import User

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
