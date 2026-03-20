from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json

router = APIRouter()

# Initialize Firebase only once
if not firebase_admin._apps:
    # Try to load from file first, then from environment variable
    key_path = "firebase_key.json"
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
    else:
        # Load from environment variable (for Railway deployment)
        firebase_config = json.loads(os.environ.get("FIREBASE_KEY", "{}"))
        cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ─── Request Models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str  # "student", "doctor", "patient"

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    role: str  # "student", "doctor", "patient"

class ResetPasswordRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class UpdatePasswordRequest(BaseModel):
    email: str
    new_password: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(data: SignupRequest):
    """Register a new user (student, doctor, or patient)"""
    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=data.email,
            password=data.password,
            display_name=data.name,
        )

        # Save extra info in Firestore
        user_data = {
            "id": user.uid,
            "name": data.name,
            "email": data.email,
            "phoneNumber": data.phone,
            "role": data.role,
            "profilePicture": None,
            # Patient-specific fields (empty by default)
            "age": None,
            "bloodType": None,
            "height": None,
            "weight": None,
            "dateOfBirth": None,
            "socialStatus": None,
            "chronicConditions": [],
            "medications": [],
        }

        db.collection("users").document(user.uid).set(user_data)

        return {"success": True, "user": user_data}

    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(data: LoginRequest):
    """Login a user and return their profile from Firestore"""
    try:
        # Verify the user exists in Firebase Auth
        firebase_user = auth.get_user_by_email(data.email)

        # Get extra data from Firestore
        doc = db.collection("users").document(firebase_user.uid).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found")

        user_data = doc.to_dict()

        # Check role matches
        if user_data.get("role") != data.role:
            raise HTTPException(status_code=403, detail="Role mismatch")

        return {"success": True, "user": user_data}

    except auth.UserNotFoundError:
        raise HTTPException(status_code=401, detail="Account not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Send password reset email via Firebase"""
    try:
        # Check user exists first
        auth.get_user_by_email(data.email)
        # Firebase handles sending the reset email via client SDK
        # On the backend we just confirm the user exists
        return {
            "success": True,
            "message": "If this email is registered, a reset link has been sent.",
        }
    except auth.UserNotFoundError:
        # Don't reveal whether email exists for security
        return {
            "success": True,
            "message": "If this email is registered, a reset link has been sent.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
