from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models import DoctorSchedule, User

load_dotenv()

SQL_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/graduation")
if SQL_URL.startswith("postgres://"):
    SQL_URL = SQL_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQL_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- Doctors ---")
doctors = db.query(User).filter(User.role == "doctor").all()
for d in doctors:
    print(f"ID: {d.id}, UID: {d.uid}, Name: {d.name}, Role: {d.role}")

print("\n--- Doctor Schedules ---")
schedules = db.query(DoctorSchedule).all()
for s in schedules:
    print(f"ID: {s.id}, DoctorID: {s.doctor_id}, Day: {s.day}, Start: {s.start_time}, End: {s.end_time}, Booked: {s.is_booked}")

db.close()
