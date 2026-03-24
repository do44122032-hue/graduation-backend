from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models import LabResult, User

load_dotenv()

SQL_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/graduation")
if SQL_URL.startswith("postgres://"):
    SQL_URL = SQL_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQL_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- Lab Results ---")
results = db.query(LabResult).all()
for r in results:
    print(f"ID: {r.id}, PatientID: {r.patient_id}, Date: {r.date}, Image: {r.image_url}")

print("\n--- Users (Patients) ---")
patients = db.query(User).filter(User.role == "patient").all()
for p in patients:
    print(f"ID: {p.id}, UID: {p.uid}, Name: {p.name}, Email: {p.email}")

db.close()
