from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Appointment, VitalSign, MedicationRecord, LabResult

router = APIRouter()

# ─── Endpoints ───────────────────────────────────────────────────────────

@router.get("/patient/{uid}")
async def get_patient_dashboard(uid: str, db: Session = Depends(get_db)):
    # Lookup user
    user = db.query(User).filter(User.id == int(uid) if uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == uid).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # In a real application, you would query these based on user.id
    # For now, we'll return mock data structured from the database models
    # if the tables are empty, or actual data if it exists.
    
    appointments = db.query(Appointment).filter(Appointment.patient_id == user.id).all()
    # If no appointments in DB, provide some mock ones for the UI to be interactive initially
    if not appointments:
        mock_apt1 = Appointment(patient_id=user.id, doctor_name="Dr. Michael Chen", specialty="Cardiologist", date="Jan 12, 2026", time="10:30 AM", type="Video Consultation", status="confirmed")
        mock_apt2 = Appointment(patient_id=user.id, doctor_name="Dr. Sarah Wilson", specialty="Dermatologist", date="Jan 15, 2026", time="02:00 PM", type="In-Person Visit", status="confirmed")
        db.add_all([mock_apt1, mock_apt2])
        db.commit()
        db.refresh(mock_apt1)
        db.refresh(mock_apt2)
        appointments = [mock_apt1, mock_apt2]

    vitals = db.query(VitalSign).filter(VitalSign.patient_id == user.id).order_by(VitalSign.id.desc()).all()
         
    medications = db.query(MedicationRecord).filter(MedicationRecord.patient_id == user.id).all()
    
    lab_results = db.query(LabResult).filter(LabResult.patient_id == user.id).order_by(LabResult.id.desc()).all()

    # Health Alert Logic (Simple example)
    health_alerts = []
    latest_vital = vitals[0] if vitals else None
    if latest_vital and (latest_vital.blood_pressure_sys > 130 or latest_vital.blood_pressure_dia > 85):
        health_alerts.append({
            "title": "Blood Pressure Alert",
            "message": f"Your last reading was {latest_vital.blood_pressure_sys}/{latest_vital.blood_pressure_dia}. Please monitor closely.",
            "icon": "warning",
            "type": "danger"
        })

    return {
        "success": True,
        "upcomingAppointments": [a.to_dict() for a in appointments],
        "recentVitals": [v.to_dict() for v in vitals],
        "activeMedications": [m.to_dict() for m in medications],
        "labResults": [l.to_dict() for l in lab_results],
        "healthAlerts": health_alerts
    }

class VitalSignCreate(BaseModel):
    uid: str
    bloodPressureSys: int
    bloodPressureDia: int
    heartRate: int
    temperature: float
    respiratoryRate: int
    oxygenSaturation: int
    weight: int
    bmi: float
    bloodGlucose: int

@router.post("/vitals")
async def log_vitals(data: VitalSignCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(data.uid) if data.uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == data.uid).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    from datetime import datetime
    current_date = datetime.now().strftime("%b %d")

    new_vital = VitalSign(
        patient_id=user.id,
        date=current_date,
        blood_pressure_sys=data.bloodPressureSys,
        blood_pressure_dia=data.bloodPressureDia,
        heart_rate=data.heartRate,
        temperature=data.temperature,
        respiratory_rate=data.respiratoryRate,
        oxygen_saturation=data.oxygenSaturation,
        weight=data.weight,
        bmi=data.bmi,
        blood_glucose=data.bloodGlucose
    )
    
    db.add(new_vital)
    db.commit()
    db.refresh(new_vital)
    
    return {"success": True, "message": "Vitals logged successfully", "vital": new_vital.to_dict()}

class LabResultCreate(BaseModel):
    uid: str
    date: str
    image: Optional[str] = None
    extractedData: Optional[dict] = None
    glucose: Optional[int] = None

@router.post("/lab-results")
async def log_lab_result(data: LabResultCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(data.uid) if data.uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == data.uid).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_lab_result = LabResult(
        patient_id=user.id,
        date=data.date,
        image_url=data.image,
        extracted_data=data.extractedData,
        glucose_level=data.glucose
    )
    
    db.add(new_lab_result)
    db.commit()
    db.refresh(new_lab_result)
    
    return {"success": True, "message": "Lab result saved successfully", "labResult": new_lab_result.to_dict()}
