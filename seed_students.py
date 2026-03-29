from database import SessionLocal
from models import User
from routers.auth import get_password_hash
import uuid

def seed_students():
    db = SessionLocal()
    try:
        students = [
            {
                "name": "Student A",
                "email": "student.a@cihanuniversity.edu.iq",
                "password": "password123",
                "phone": "07501112233",
            },
            {
                "name": "Student B",
                "email": "student.b@cihanuniversity.edu.iq",
                "password": "password123",
                "phone": "07504445566",
            }
        ]
        
        for s in students:
            # Check if exists
            exists = db.query(User).filter(User.email == s["email"]).first()
            if not exists:
                new_user = User(
                    uid=str(uuid.uuid4()),
                    name=s["name"],
                    email=s["email"],
                    password_hash=get_password_hash(s["password"]),
                    phone=s["phone"],
                    role="student",
                    is_active=True, # Active by default for test users
                    chronic_conditions=[],
                    medications=[]
                )
                db.add(new_user)
                print(f"Added student: {s['name']} ({s['email']})")
            else:
                print(f"Student already exists: {s['email']}")
        
        db.commit()
    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_students()
