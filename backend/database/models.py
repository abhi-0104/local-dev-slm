from sqlalchemy import Column, Integer, String, DateTime, ForeignKey # <-- Added ForeignKey here
from datetime import datetime, timezone
from backend.database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee") 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- NEW CODE BELOW ---
class UserSession(Base):
    """Stores the active login tokens for users."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    # The ForeignKey strictly enforces that this ID must exist in the users table!
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# --- AI CONVERSATION MODELS BELOW ---

class Conversation(Base):
    """A folder holding a chat session between an employee and the AI."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, default="New Conversation")
    # Which model was used (e.g., 'llama3.2:3b' or 'dual-loop')
    model = Column(String, nullable=False) 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Message(Base):
    """An individual message (either from the human or the AI)."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    # Role can be: 'system', 'user', or 'assistant' (Standard AI formats)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ActivityLog(Base):
    """Security/Compliance log for IT Admins."""
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False) # e.g., "Generated Code", "Logged In"
    model = Column(String, nullable=True) # Which AI they used
    details = Column(String, nullable=True) # Extra info (like tokens/sec)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Feedback(Base):
    """Stores the Human-in-the-Loop review data."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_code = Column(String, nullable=False)
    feedback_text = Column(String, nullable=False) # What the human told the AI to fix
    improved_code = Column(String, nullable=True)
    approved = Column(Integer, default=0) # 0 for False, 1 for True (SQLite uses integers for booleans)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))