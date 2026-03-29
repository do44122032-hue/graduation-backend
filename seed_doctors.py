from database import SessionLocal
from models import User
from routers.auth import get_password_hash
import uuid

def seed_doctors():
    db = SessionLocal()
    try:
        doctors = [
            {
                "name": "Dr. Sarah Williams",
                "email": "sarah.williams@cihanuniversity.edu.iq",
                "password": "password123",
                "phone": "07501112233",
            },
            {
                "name": "Dr. James Wilson",
                "email": "james.wilson@cihanuniversity.edu.iq",
                "password": "password123",
                "phone": "07504445566",
            }
        ]
        
        for d in doctors:
            # Check if exists
            exists = db.query(User).filter(User.email == d["email"]).first()
            if not exists:
                new_user = User(
                    uid=str(uuid.uuid4()),
                    name=d["name"],
                    email=d["email"],
                    password_hash=get_password_hash(d["password"]),
                    phone=d["phone"],
                    role="doctor",
                    is_active=True,
                    chronic_conditions=[],
                    medications=[]
                )
                db.add(new_user)
                print(f"Added doctor: {d['name']} ({d['email']})")
            else:
                print(f"Doctor already exists: {d['email']}")
        
        db.commit()
    except Exception as e:
        print(f"Error seeding doctors: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_doctors()
