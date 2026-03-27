
from database import SessionLocal
from models import User, VitalSign
import sys

def check_vitals(user_id_or_uid):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(user_id_or_uid) if user_id_or_uid.isdigit() else False).first()
        if not user:
            user = db.query(User).filter(User.uid == user_id_or_uid).first()
        
        if not user:
            print(f"User {user_id_or_uid} not found.")
            return

        print(f"User found: ID={user.id}, UID={user.uid}, Name={user.name}")
        
        vitals = db.query(VitalSign).filter(VitalSign.patient_id == user.id).order_by(VitalSign.id.desc()).all()
        print(f"Found {len(vitals)} vital records.")
        for v in vitals[:5]:
            print(f"  - ID={v.id}, Date={v.date}, BP={v.blood_pressure_sys}/{v.blood_pressure_dia}, HR={v.heart_rate}")

    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_vitals(sys.argv[1])
    else:
        print("Please provide user ID or UID.")
