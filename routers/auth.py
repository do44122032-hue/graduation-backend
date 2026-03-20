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

class ResetPasswordRequest(BaseModel):
    email: str


# ─── Endpoints ───────────────────────────────────────────────────────────

@router.post("/signup")
async def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    new_user = User(
        uid=str(uuid.uuid4()),
        name=data.name,
        email=data.email,
        password_hash=get_password_hash(data.password),
        phone=data.phone,
        role=data.role,
        chronic_conditions=[],
        medications=[]
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"success": True, "user": new_user.to_dict()}


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == data.email).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(data.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if db_user.role != data.role:
        raise HTTPException(status_code=403, detail="Unauthorized role")
        
    return {"success": True, "user": db_user.to_dict()}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    # In a real app, send email; here we just check if exists
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user:
        return {"success": True, "message": "Reset instructions sent (Mock)"}
    return {"success": True}  # Security: don't leak user presence
