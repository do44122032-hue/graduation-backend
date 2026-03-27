
from database import SessionLocal
from models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("Available Users in Database:")
        print(f"{'ID':<5} | {'UID':<30} | {'Name':<20} | {'Role':<10}")
        print("-" * 75)
        for u in users:
            print(f"{u.id:<5} | {u.uid:<30} | {u.name:<20} | {u.role:<10}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
