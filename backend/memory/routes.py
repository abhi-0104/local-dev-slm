from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database.db import get_db
from backend.database.models import User, Conversation, Message
from backend.schemas.responses import ConversationListResponse, ConversationDetailResponse
from backend.auth.utils import get_current_user

router = APIRouter(prefix="/history", tags=["History & Memory"])

@router.get("/", response_model=List[ConversationListResponse])
def get_user_conversations(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Returns a list of all chat folders for the logged-in user."""
    
    # Grab all conversations belonging to this user, ordered by newest first
    conversations = db.query(Conversation)\
        .filter(Conversation.user_id == current_user.id)\
        .order_by(Conversation.created_at.desc())\
        .all()
        
    return conversations


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(
    conversation_id: int,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Opens a specific folder and returns all messages inside it."""
    
    # 1. Find the conversation
    conversation = db.query(Conversation)\
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)\
        .first()
        
    # Security: If it doesn't exist, or belongs to another employee, kick them out!
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    # 2. Grab all the messages inside it, ordered oldest to newest (like a chat app)
    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.asc())\
        .all()
        
    # 3. Package it up for the frontend
    return ConversationDetailResponse.model_validate({**conversation.__dict__, "messages": messages})