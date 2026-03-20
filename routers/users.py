from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from firebase_admin import firestore

router = APIRouter()
db = firestore.client()


# ─── Request Models ───────────────────────────────────────────────────────────

class PatientProfileUpdate(BaseModel):
    uid: str
    age: Optional[str] = None
    bloodType: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    dateOfBirth: Optional[str] = None
    socialStatus: Optional[str] = None
    chronicConditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/profile/{uid}")
async def get_profile(uid: str):
    """Get user profile by Firebase UID"""
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return doc.to_dict()


@router.put("/patient-profile")
async def update_patient_profile(data: PatientProfileUpdate):
    """Update patient medical profile fields"""
    try:
        update_data = data.dict(exclude={"uid"}, exclude_none=True)
        db.collection("users").document(data.uid).update(update_data)
        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/role/{uid}")
async def get_user_role(uid: str):
    """Get the role of a user by UID"""
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return {"role": doc.to_dict().get("role")}
