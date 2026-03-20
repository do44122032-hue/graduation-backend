from sqlalchemy import Column, String, Integer, ARRAY, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)  # Legacy or for JWT compatibility
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String)
    role = Column(String, nullable=False)  # "student", "doctor", "patient"
    profile_picture = Column(String)

    # Medical Profile (flattened for simplicity, or could be a JSON column)
    age = Column(String)
    blood_type = Column(String)
    height = Column(String)
    weight = Column(String)
    dob = Column(String)
    social_status = Column(String)
    chronic_conditions = Column(JSON, default=[])
    medications = Column(JSON, default=[])

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phoneNumber": self.phone,
            "profilePicture": self.profile_picture,
            "age": self.age,
            "bloodType": self.blood_type,
            "height": self.height,
            "weight": self.weight,
            "dateOfBirth": self.dob,
            "socialStatus": self.social_status,
            "chronicConditions": self.chronic_conditions or [],
            "medications": self.medications or [],
        }
