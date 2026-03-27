from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models import StudentTask, User

# Load environment variables
load_dotenv()

# Use the same database URL as the main application
SQL_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/graduation")
if SQL_URL.startswith("postgres://"):
    SQL_URL = SQL_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQL_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed_tasks():
    # Check if tasks already exist
    existing = db.query(StudentTask).first()
    if existing:
        print("Tasks already seeded. Skipping.")
        return

    sample_tasks = [
        {
            "title": "Endocrinology Research",
            "description": "Complete the research paper on Thyroid disorders and their impact on patient metabolism.",
            "due_date": "2024-11-15",
            "color_hex": "E8C998"
        },
        {
            "title": "Anatomy Quiz Prep",
            "description": "Review cardiovascular system anatomy for the upcoming mock exam.",
            "due_date": "2024-11-20",
            "color_hex": "98B9E8"
        },
        {
            "title": "Clinical Case Study #4",
            "description": "Analyze the patient case for diabetes type 2 management plan.",
            "due_date": "2024-11-25",
            "color_hex": "E89898"
        }
    ]

    print(f"Seeding {len(sample_tasks)} global student tasks...")

    for task_data in sample_tasks:
        task = StudentTask(
            student_id=None, # Global tasks for all students
            title=task_data["title"],
            description=task_data["description"],
            due_date=task_data["due_date"],
            color_hex=task_data["color_hex"],
            status="pending"
        )
        db.add(task)
    
    db.commit()
    print("Seeding complete!")

if __name__ == "__main__":
    seed_tasks()
    db.close()
