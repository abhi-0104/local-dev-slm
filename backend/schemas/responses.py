from pydantic import BaseModel
from datetime import datetime
from typing import List

class MessageResponse(BaseModel):
    """Shape of a single chat bubble."""
    id: int
    role: str # 'user' or 'assistant'
    content: str
    created_at: datetime

class ConversationListResponse(BaseModel):
    """Shape of a folder shown in the sidebar."""
    id: int
    title: str
    model: str
    created_at: datetime

class ConversationDetailResponse(BaseModel):
    """Shape of a fully opened folder with all its messages."""
    id: int
    title: str
    messages: List[MessageResponse] # A list of all chat bubbles!