from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Appointment, VitalSign, MedicationRecord, LabResult, DoctorSchedule
from datetime import datetime
import traceback

router = APIRouter()

# ─── Endpoints ───────────────────────────────────────────────────────────

@router.get("/patient/{uid}")
async def get_patient_dashboard(uid: str, db: Session = Depends(get_db)):
    try:
        # Lookup user
        user = db.query(User).filter(User.id == int(uid) if uid.isdigit() else False).first()
        if not user:
            user = db.query(User).filter(User.uid == uid).first()
            
        if not user:
            return {"success": False, "error": "User not found"}
            
        # Fetching data
        appointments = db.query(Appointment).filter(Appointment.patient_id == user.id).all()
        vitals = db.query(VitalSign).filter(VitalSign.patient_id == user.id).order_by(VitalSign.id.desc()).all()
        medications = db.query(MedicationRecord).filter(MedicationRecord.patient_id == user.id).all()
        lab_results = db.query(LabResult).filter(LabResult.patient_id == user.id).order_by(LabResult.id.desc()).all()

        # Health Alert Logic (Backend side)
        health_alerts = []
        latest_vital = vitals[0] if vitals else None
        
        if latest_vital:
            sys = latest_vital.blood_pressure_sys
            dia = latest_vital.blood_pressure_dia
            
            # Systolic > 130 or Diastolic > 85 triggers an alert
            if (sys and sys > 130) or (dia and dia > 85):
                health_alerts.append({
                    "title": "High Blood Pressure Alert",
                    "message": f"Your last reading was {sys}/{dia}. Please monitor closely.",
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
    except Exception as e:
        print(f"CRITICAL ERROR in get_patient_dashboard: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False, 
            "error": f"Internal Server Error: {str(e)}",
            "details": traceback.format_exc() if os.getenv("DEBUG") else "Enabled debug for full trace"
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
    try:
        user = db.query(User).filter(User.id == int(data.uid) if data.uid.isdigit() else False).first()
        if not user:
            user = db.query(User).filter(User.uid == data.uid).first()
            
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        from datetime import datetime
        current_date = datetime.now().strftime("%b %d %Y") # Full date for better sorting

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
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/debug/all-vitals")
async def get_all_vitals_debug(db: Session = Depends(get_db)):
    """Debug endpoint to see everything in the vital_signs table"""
    vitals = db.query(VitalSign).all()
    return {"count": len(vitals), "data": [v.to_dict() for v in vitals]}

# (Rest of the file remains same, keeping log_lab_result, book_appointment etc)
import os
from models import LabResult, MedicationRecord

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

class AppointmentCreate(BaseModel):
    uid: str
    patientName: Optional[str] = None
    doctorId: Optional[str] = None
    doctorName: str
    specialty: str
    date: str
    time: str
    type: str

@router.post("/appointments/book")
async def book_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(data.uid) if data.uid.isdigit() else False).first()
    if not user:
        user = db.query(User).filter(User.uid == data.uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    doctor_id_val = int(data.doctorId) if data.doctorId and data.doctorId.isdigit() else None
    new_appointment = Appointment(
        patient_id=user.id,
        patient_name=data.patientName,
        doctor_id=doctor_id_val,
        doctor_name=data.doctorName,
        specialty=data.specialty,
        date=data.date,
        time=data.time,
        type=data.type,
        status="pending"
    )
    db.add(new_appointment)
    if doctor_id_val:
        try:
            day_name = datetime.strptime(data.date, "%Y-%m-%d").strftime("%A")
            slot = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor_id_val, DoctorSchedule.day == day_name, DoctorSchedule.start_time == data.time).first()
            if slot: slot.is_booked = True
        except: pass
    db.commit()
    db.refresh(new_appointment)
    return {"success": True, "message": "Appointment booked successfully", "appointment": new_appointment.to_dict()}

@router.get("/doctor/{uid}/appointments")
async def get_doctor_appointments(uid: str, db: Session = Depends(get_db)):
    doctor = db.query(User).filter(User.id == int(uid) if uid.isdigit() else False).first()
    if not doctor: doctor = db.query(User).filter(User.uid == uid).first()
    if not doctor or doctor.role != "doctor": raise HTTPException(status_code=404, detail="Doctor not found")
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor.id).all()
    return [a.to_dict() for a in appointments]

@router.post("/appointments/cancel/{appt_id}")
async def cancel_appointment(appt_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appointment: raise HTTPException(status_code=404, detail="Appointment not found")
    appointment.status = "cancelled"
    if appointment.doctor_id:
        try:
            day_name = datetime.strptime(appointment.date, "%Y-%m-%d").strftime("%A")
            slot = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == appointment.doctor_id, DoctorSchedule.day == day_name, DoctorSchedule.start_time == appointment.time).first()
            if slot: slot.is_booked = False
        except: pass
    db.commit()
    db.refresh(appointment)
    return {"success": True, "message": "Appointment cancelled successfully", "appointment": appointment.to_dict()}

@router.post("/appointments/confirm/{appt_id}")
async def confirm_appointment(appt_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appointment: raise HTTPException(status_code=404, detail="Appointment not found")
    appointment.status = "confirmed"
    db.commit()
    db.refresh(appointment)
    return {"success": True, "message": "Appointment confirmed successfully", "appointment": appointment.to_dict()}
