from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from backend.database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="employee") 
    
    # We use a 'lambda' function here. This tells SQLAlchemy: 
    # "Don't calculate the time right now. Wait until the exact millisecond 
    # a new user is created, and THEN run this timezone-aware function."
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))