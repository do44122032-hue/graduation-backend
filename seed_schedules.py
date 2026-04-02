from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models import DoctorSchedule, User

# Load environment variables
load_dotenv()

# Use the same database URL as the main application - default to local SQLite for development
SQL_URL = os.getenv("DATABASE_URL", "sqlite:///./graduation.db")
if SQL_URL.startswith("postgres://"):
    SQL_URL = SQL_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs special arguments
if SQL_URL.startswith("sqlite"):
    engine = create_engine(SQL_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQL_URL)
    
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed_schedules():
    doctors = db.query(User).filter(User.role == "doctor").all()
    if not doctors:
        print("No doctors found to seed schedules for!")
        return

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    times = ["09:00 AM", "10:00 AM", "11:00 AM", "01:00 PM", "02:00 PM", "03:00 PM"]

    print(f"Found {len(doctors)} doctors. Seeding schedules...")

    for doctor in doctors:
        # Check if doctor already has schedules
        existing = db.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor.id).first()
        if existing:
            print(f"Doctor {doctor.name} already has schedules. Skipping.")
            continue

        for day in days:
            for time in times:
                # Add a slot
                slot = DoctorSchedule(
                    doctor_id=doctor.id,
                    day=day,
                    start_time=time,
                    end_time=time.replace("00", "30"), # Mock end time
                    is_booked=False
                )
                db.add(slot)
    
    db.commit()
    print("Seeding complete! Now patients should see available slots.")

if __name__ == "__main__":
    seed_schedules()
    db.close()
