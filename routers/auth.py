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


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    import random
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
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
        
        # Email Integration (Gmail SMTP)
        smtp_email = os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if smtp_email and smtp_password:
            try:
                # Setup Email Message
                msg = MIMEMultipart()
                msg['From'] = smtp_email
                msg['To'] = db_user.email
                msg['Subject'] = "MyChart Password Reset Code"
                
                body = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                    <h2>Password Reset Request</h2>
                    <p>Hello {db_user.name},</p>
                    <p>We received a request to reset your MyChart password. Your One-Time Password (OTP) is:</p>
                    <h1 style="color: #4CAF50; letter-spacing: 5px; font-size: 32px;">{code}</h1>
                    <p><i>Note: This code will expire in exactly 5 minutes.</i></p>
                    <p>If you did not request this, please ignore this email.</p>
                </div>
                """
                msg.attach(MIMEText(body, 'html'))
                
                # Connect to Gmail SMTP Sever
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(smtp_email, smtp_password)
                text = msg.as_string()
                server.sendmail(smtp_email, db_user.email, text)
                server.quit()
                print(f"DEBUG: Email OTP sent successfully to {db_user.email}")
                
            except Exception as e:
                print(f"DEBUG: Failed to send Email OTP: {e}")
                # We still return success but maybe the server fails logging
        else:
            print(f"DEBUG: No SMTP Keys. Code for {db_user.email}: {code}")
            
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
