from sqlalchemy import Column, String, Integer, ARRAY, Text, ForeignKey, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

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
    department = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)

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
            "department": self.department,
            "bio": self.bio,
            "isActive": self.is_active,
        }

class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    day = Column(String) # e.g., 'Monday'
    start_time = Column(String) # e.g., '09:00 AM'
    end_time = Column(String) # e.g., '10:00 AM'
    is_booked = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "doctorId": self.doctor_id,
            "day": self.day,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "isBooked": self.is_booked,
        }

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    patient_name = Column(String, nullable=True) # Cached name for easy display
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Linked to doctor user
    doctor_name = Column(String) # Simple for now, can be linked to doctor user id later
    specialty = Column(String)
    date = Column(String)
    time = Column(String)
    type = Column(String) # 'Video Consultation', 'In-Person Visit'
    status = Column(String) # 'confirmed', 'pending', 'cancelled'

    def to_dict(self):
        return {
            "id": str(self.id),
            "patientId": self.patient_id,
            "patientName": self.patient_name,
            "doctorId": self.doctor_id,
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
    temperature = Column(Float) # or Float
    respiratory_rate = Column(Integer)
    oxygen_saturation = Column(Integer)
    weight = Column(Integer)
    bmi = Column(Float) # or Float
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

class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String)
    image_url = Column(String)
    extracted_data = Column(JSON)
    glucose_level = Column(Integer, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "image": self.image_url,
            "extractedData": self.extracted_data,
            "glucose": self.glucose_level
        }

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    timestamp = Column(String, default=lambda: datetime.now().isoformat())
    type = Column(String, default="text") # text, lab_result, medication, appointment
    data = Column(JSON, nullable=True) # For non-text message details

    def to_dict(self):
        return {
            "id": self.id,
            "senderId": self.sender_id,
            "receiverId": self.receiver_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "type": self.type,
            "data": self.data or {}
        }

class StudentReport(Base):
    __tablename__ = "student_reports"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    file_url = Column(String, nullable=True)
    status = Column(String, default="submitted")
    submitted_at = Column(String, default=lambda: datetime.now().isoformat())

    def to_dict(self):
        return {
            "id": self.id,
            "studentId": self.student_id,
            "doctorId": self.doctor_id,
            "title": self.title,
            "description": self.description,
            "fileUrl": self.file_url,
            "status": self.status,
            "submittedAt": self.submitted_at
        }

class StudentTask(Base):
    __tablename__ = "student_tasks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String)
    due_date = Column(String)
    color_hex = Column(String)
    file_url = Column(String, nullable=True) # Added for task documents
    status = Column(String, default="pending")

    def to_dict(self):
        return {
            "id": self.id,
            "studentId": self.student_id,
            "doctorId": self.doctor_id,
            "title": self.title,
            "description": self.description,
            "dueDate": self.due_date,
            "colorHex": self.color_hex,
            "fileUrl": self.file_url,
            "status": self.status
        }

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    instructor = Column(String)
    color_hex = Column(String, default="E8C998")
    icon_name = Column(String, default="school")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "instructor": self.instructor,
            "colorHex": self.color_hex,
            "iconName": self.icon_name,
        }

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    progress = Column(Float, default=0.0)
    grade = Column(String, default="Pending")
    next_class = Column(String)

    def to_dict(self):
        return {
            "id": self.id,
            "studentId": self.student_id,
            "courseId": self.course_id,
            "progress": self.progress,
            "grade": self.grade,
            "nextClass": self.next_class,
        }
