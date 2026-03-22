import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, SessionLocal
from models import User, Appointment, VitalSign, MedicationRecord
import uuid

# Use a test database or an in-memory SQLite if configured, 
# here we'll assume the current database config for simplicity of testing on Railway locally.
client = TestClient(app)

def setup_module(module):
    # Base.metadata.create_all(bind=engine)
    pass

def teardown_module(module):
    # Clean up test data if needed
    pass

def test_patient_dashboard_empty():
    # Attempt to fetch dashboard for a non-existent user
    response = client.get("/dashboard/patient/999999")
    assert response.status_code == 404

def test_create_and_fetch_patient_dashboard():
    # 1. Create a mock user
    test_uid = str(uuid.uuid4())
    db = SessionLocal()
    new_user = User(
        uid=test_uid,
        name="Test Patient",
        email=f"test_{test_uid}@example.com",
        password_hash="hashed_pw",
        role="patient"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user_id = new_user.id
    db.close()

    # 2. Fetch dashboard (should auto-create mock data per our logic)
    response = client.get(f"/dashboard/patient/{user_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "upcomingAppointments" in data
    assert "recentVitals" in data
    assert "activeMedications" in data
    
    # Check mock data was generated
    assert len(data["upcomingAppointments"]) > 0
    assert len(data["recentVitals"]) > 0
    assert len(data["activeMedications"]) > 0

def test_log_vitals():
    # 1. Create a mock user
    test_uid = str(uuid.uuid4())
    db = SessionLocal()
    new_user = User(
        uid=test_uid,
        name="Test Patient 2",
        email=f"test2_{test_uid}@example.com",
        password_hash="hashed_pw",
        role="patient"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user_id = new_user.id
    db.close()

    # 2. Log vitals
    vital_data = {
        "uid": str(user_id),
        "bloodPressureSys": 120,
        "bloodPressureDia": 80,
        "heartRate": 75,
        "temperature": 98.6,
        "respiratoryRate": 16,
        "oxygenSaturation": 99,
        "weight": 145,
        "bmi": 23.5,
        "bloodGlucose": 90
    }
    response = client.post("/dashboard/vitals", json=vital_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Vitals logged successfully"
    assert data["vital"]["bloodPressureSys"] == 120
