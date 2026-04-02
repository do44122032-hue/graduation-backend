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
    phone: str

class VerifyCodeRequest(BaseModel):
    phone: str
    code: str

class UpdatePasswordRequest(BaseModel):
    phone: str
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
    # Query by phone
    db_user = db.query(User).filter(User.phone == data.phone).first()
    
    if db_user:
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        db_user.reset_code = code
        db.commit()
        # In a real app, send actual SMS here.
        print(f"DEBUG: Reset code for phone {data.phone} is {code}")
        return {"success": True, "message": "Reset code generated"}
    
    # Still return success to prevent user enumeration
    return {"success": True, "message": "Phone number not found but we'll pretend it is for security"}

@router.post("/verify-code")
async def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == data.phone).first()
    
    if not db_user or db_user.reset_code != data.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    return {"success": True}

@router.post("/update-password")
async def update_password(data: UpdatePasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.phone == data.phone).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not db_user.reset_code:
         raise HTTPException(status_code=400, detail="Password reset was not initiated")

    db_user.password_hash = get_password_hash(data.new_password)
    db_user.reset_code = None # Clear code after use
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
