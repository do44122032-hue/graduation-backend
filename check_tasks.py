from database import SessionLocal
from models import StudentTask
import sys

def check_tasks():
    db = SessionLocal()
    try:
        tasks = db.query(StudentTask).all()
        print(f"Found {len(tasks)} tasks in the database.")
        for t in tasks:
            print(f"  - ID={t.id}, Title={t.title}, Status={t.status}")
    except Exception as e:
        print(f"Error checking tasks: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_tasks()
