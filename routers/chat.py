from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from database import get_db
from models import User, Message

router = APIRouter()

class MessageCreate(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    type: str = "text"
    data: Optional[dict] = None

@router.post("/send")
async def send_message(data: MessageCreate, db: Session = Depends(get_db)):
    # Verify both users exist (handling both integer id and string uid)
    sender = db.query(User).filter(User.id == int(data.sender_id) if data.sender_id.isdigit() else False).first()
    if not sender:
        sender = db.query(User).filter(User.uid == data.sender_id).first()
        
    receiver = db.query(User).filter(User.id == int(data.receiver_id) if data.receiver_id.isdigit() else False).first()
    if not receiver:
        receiver = db.query(User).filter(User.uid == data.receiver_id).first()
    
    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="One or both users not found")
        
    new_message = Message(
        sender_id=sender.id,
        receiver_id=receiver.id,
        content=data.content,
        type=data.type,
        data=data.data
    )
    
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return {"success": True, "message": new_message.to_dict()}

@router.get("/history/{user1_id}/{user2_id}")
async def get_chat_history(user1_id: str, user2_id: str, db: Session = Depends(get_db)):
    # Get actual integer IDs
    u1 = db.query(User).filter(User.id == int(user1_id) if user1_id.isdigit() else False).first()
    if not u1: u1 = db.query(User).filter(User.uid == user1_id).first()
    
    u2 = db.query(User).filter(User.id == int(user2_id) if user2_id.isdigit() else False).first()
    if not u2: u2 = db.query(User).filter(User.uid == user2_id).first()
    
    if not u1 or not u2:
        return []
        
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == u1.id, Message.receiver_id == u2.id),
            and_(Message.sender_id == u2.id, Message.receiver_id == u1.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    return [m.to_dict() for m in messages]

@router.get("/conversations/{user_id}")
async def get_conversations(user_id: str, db: Session = Depends(get_db)):
    # Get actual integer ID
    u = db.query(User).filter(User.id == int(user_id) if user_id.isdigit() else False).first()
    if not u: u = db.query(User).filter(User.uid == user_id).first()
    
    if not u:
        return []
        
    actual_user_id = u.id
    
    # 1. Find all unique partners
    sent_to = db.query(Message.receiver_id).filter(Message.sender_id == actual_user_id).distinct().all()
    received_from = db.query(Message.sender_id).filter(Message.receiver_id == actual_user_id).distinct().all()
    
    partner_ids = set([r[0] for r in sent_to] + [r[0] for r in received_from])
    
    conversations = []
    for p_id in partner_ids:
        partner = db.query(User).filter(User.id == p_id).first()
        if not partner:
            continue
            
        # Get last message
        last_msg = db.query(Message).filter(
            or_(
                and_(Message.sender_id == actual_user_id, Message.receiver_id == p_id),
                and_(Message.sender_id == p_id, Message.receiver_id == actual_user_id)
            )
        ).order_by(Message.timestamp.desc()).first()
        
        conversations.append({
            "partner": partner.to_dict(),
            "lastMessage": last_msg.to_dict() if last_msg else None,
            "unreadCount": 0 # Simple implementation for now
        })
        
    # Sort by last message timestamp
    conversations.sort(key=lambda x: x["lastMessage"]["timestamp"] if x["lastMessage"] else "", reverse=True)
    
    return conversations
