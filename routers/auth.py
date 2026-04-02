from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User
from passlib.context import CryptContext
import uuid

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Auth Logic ───────────────────────────────────────────────────────────

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# ─── Request Models ───────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    role: str
    department: str | None = None
    bio: str | None = None

class ResetPasswordRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class UpdatePasswordRequest(BaseModel):
    email: str
    new_password: str

class LogoutRequest(BaseModel):
    uid: str



# ─── Endpoints ───────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    email_lower = data.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        uid=str(uuid.uuid4()),
        name=data.name,
        email=email_lower,
        password_hash=get_password_hash(data.password),
        phone=data.phone,
        role=data.role,
        department=data.department,
        bio=data.bio,
        is_active=False,
        chronic_conditions=[],
        medications=[]
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"success": True, "user": new_user.to_dict()}


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    email_lower = data.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(data.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if db_user.role != data.role:
        raise HTTPException(status_code=403, detail="Unauthorized role")
        
    # Activate user on first successful login
    if not db_user.is_active:
        db_user.is_active = True
        db.commit()
        db.refresh(db_user)
        
    return {"success": True, "user": db_user.to_dict()}


from fastapi import BackgroundTasks

def send_email_background(script_url, target_email, target_name, code):
    import requests
    import json
    
    try:
        html_body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2>Password Reset Request</h2>
            <p>Hello {target_name},</p>
            <p>We received a request to reset your MyChart password. Your One-Time Password (OTP) is:</p>
            <h1 style="color: #4CAF50; letter-spacing: 5px; font-size: 32px;">{code}</h1>
            <p><i>Note: This code will expire in exactly 5 minutes.</i></p>
            <p>If you did not request this, please ignore this email.</p>
        </div>
        """
        
        payload = {
            "to": target_email,
            "subject": "MyChart Password Reset Code",
            "htmlBody": html_body
        }
        
        # Use HTTP POST (Port 443) which Railway never blocks!
        response = requests.post(script_url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print(f"DEBUG: Webhook Email sent successfully to {target_email}!")
        else:
            print(f"DEBUG: Webhook failed. Code: {response.status_code}, Body: {response.text}")
            
    except Exception as e:
        print(f"DEBUG: Failed to trigger Google Script: {e}")

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    import random
    from datetime import datetime, timedelta, timezone
    import os

    # Query by email
    email_lower = data.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    
    if db_user:
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        db_user.reset_code = code
        # Set exact expiration time (5 minutes from now)
        db_user.reset_code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        db.commit()
        
        # Google Apps Script Webhook
        script_url = os.getenv("GOOGLE_SCRIPT_URL")
        
        if script_url:
            # Send email in the background to prevent client timeout!
            background_tasks.add_task(send_email_background, script_url, db_user.email, db_user.name, code)
        else:
            print(f"DEBUG: No Script URL. Code for {db_user.email}: {code}")
            
        return {"success": True, "message": "Reset code sent to your email!"}
    
    # Still return success to prevent user enumeration
    return {"success": True, "message": "Email sent if registered"}

@router.post("/verify-code")
async def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    
    email_lower = data.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    
    if not db_user or db_user.reset_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    if db_user.reset_code_expires_at:
        # Avoid python timezone dumbness by making everything UTC aware
        now_utc = datetime.now(timezone.utc)
        expire_time = db_user.reset_code_expires_at
        if expire_time.tzinfo is None:
             expire_time = expire_time.replace(tzinfo=timezone.utc)
             
        if now_utc > expire_time:
             raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")
             
    return {"success": True}

@router.post("/update-password")
async def update_password(data: UpdatePasswordRequest, db: Session = Depends(get_db)):
    email_lower = data.email.lower()
    db_user = db.query(User).filter(User.email == email_lower).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not db_user.reset_code:
         raise HTTPException(status_code=400, detail="Password reset was not initiated")

    db_user.password_hash = get_password_hash(data.new_password)
    db_user.reset_code = None # Clear code after use to prevent reuse
    db_user.reset_code_expires_at = None
    db.commit()
    
    return {"success": True, "message": "Password updated successfully"}

@router.post("/logout")
async def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == int(data.uid) if data.uid.isdigit() else False).first()
    if not db_user:
        db_user = db.query(User).filter(User.uid == data.uid).first()
        
    if db_user and db_user.role == "doctor":
        db_user.is_active = False
        db.commit()
        
    return {"success": True}
