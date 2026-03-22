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

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    doctor_name = Column(String) # Simple for now, can be linked to doctor user id later
    specialty = Column(String)
    date = Column(String)
    time = Column(String)
    type = Column(String) # 'Video Consultation', 'In-Person Visit'
    status = Column(String) # 'confirmed', 'pending', 'cancelled'

    def to_dict(self):
        return {
            "id": str(self.id),
            "doctorName": self.doctor_name,
            "specialty": self.specialty,
            "date": self.date,
            "time": self.time,
            "type": self.type,
            "status": self.status,
        }

class VitalSign(Base):
    __tablename__ = "vital_signs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String) # e.g., 'Dec 23'
    blood_pressure_sys = Column(Integer)
    blood_pressure_dia = Column(Integer)
    heart_rate = Column(Integer)
    temperature = Column(Integer) # or Float
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Integer)
    weight = Column(Integer)
    bmi = Column(Integer) # or Float
    blood_glucose = Column(Integer)

    def to_dict(self):
        return {
            "date": self.date,
            "bloodPressureSys": self.blood_pressure_sys,
            "bloodPressureDia": self.blood_pressure_dia,
            "heartRate": self.heart_rate,
            "temperature": self.temperature,
            "respiratoryRate": self.respiratory_rate,
            "oxygenSaturation": self.oxygen_saturation,
            "weight": self.weight,
            "bmi": self.bmi,
            "bloodGlucose": self.blood_glucose,
        }

class MedicationRecord(Base):
    __tablename__ = "medication_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    generic_name = Column(String)
    brand_name = Column(String)
    strength = Column(String)
    form = Column(String)
    route = Column(String)
    frequency = Column(String)
    prescribing_physician = Column(String)
    start_date = Column(String)
    reason_for_medication = Column(String)
    special_instructions = Column(String)
    
    def to_dict(self):
        return {
            "id": self.id,
            "genericName": self.generic_name,
            "brandName": self.brand_name,
            "strength": self.strength,
            "form": self.form,
            "route": self.route,
            "frequency": self.frequency,
            "prescribingPhysician": self.prescribing_physician,
            "startDate": self.start_date,
            "reasonForMedication": self.reason_for_medication,
            "specialInstructions": self.special_instructions,
        }
