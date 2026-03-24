from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from sqlalchemy.orm import Session
from database import get_db
from models import User, LabResult
import pytesseract
from PIL import Image
import io
import shutil
import os
from datetime import datetime

router = APIRouter()

# Directory to save uploaded images (for demo/local development)
UPLOAD_DIR = "static/lab_reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_lab_result(
    uid: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Lab upload request for user {uid}")
    # 1. Verify User
    user = None
    if uid.isdigit():
        user = db.query(User).filter(User.id == int(uid)).first()
    
    if not user:
        user = db.query(User).filter(User.uid == uid).first()
    
    if not user:
        print(f"DEBUG: User {uid} not found in database")
        raise HTTPException(status_code=404, detail=f"User with ID/UID '{uid}' not found")

    # 2. Save File
    file_path = os.path.join(UPLOAD_DIR, f"{user.id}_{datetime.now().timestamp()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Perform OCR
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        
        # Simple logic to find "Glucose" and a number nearby
        glucose_val = None
        lines = text.split('\n')
        for line in lines:
            if "glucose" in line.lower():
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    glucose_val = int(numbers[0])
                    break
    except Exception as e:
        print(f"OCR Error: {e}")
        text = "OCR Failed"
        glucose_val = None

    # 4. Save to Database
    try:
        new_result = LabResult(
            patient_id=user.id,
            date=datetime.now().strftime("%Y-%m-%d"),
            image_url=f"/static/lab_reports/{os.path.basename(file_path)}", # In production, use S3/Cloudinary URL
            extracted_data={"raw_text": text},
            glucose_level=glucose_val
        )
        
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        # Try to re-create tables if it's a "table doesn't exist" error
        raise HTTPException(status_code=500, detail=f"Database error while saving result. Ensure tables exist. Error: {str(e)}")

    return {"success": True, "data": new_result.to_dict()}
