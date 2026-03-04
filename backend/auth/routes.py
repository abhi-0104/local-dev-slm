from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import User, UserSession # <-- Added UserSession
from backend.auth.models import UserCreate, UserLogin, TokenResponse, LogoutRequest
from backend.auth.utils import get_password_hash, verify_password, create_session_token # <-- Added verify & create

# Create our "mini-app" for authentication
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Creates a new user in the database."""
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, password_hash=hashed_pw, role=user_data.role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "username": str(new_user.username), "role": str(new_user.role)}

# --- NEW ROUTE BELOW ---

@router.post("/login", response_model=TokenResponse)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Verifies credentials and returns a session token."""
    
    # 1. Find the user in the database
    user = db.query(User).filter(User.username == user_data.username).first()
    
    # 2. If user doesn't exist OR password math fails, kick them out
    # We use the EXACT same error message for both to prevent hackers from guessing valid usernames
    if not user or not verify_password(user_data.password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # 3. Generate the VIP Pass
    new_token = create_session_token()
    
    # 4. Save the VIP Pass to the database so we remember them
    session_record = UserSession(user_id=user.id, token=new_token)
    db.add(session_record)
    db.commit()
    
    # 5. Hand the pass back to the user
    return {"access_token": new_token, "token_type": "bearer"}

@router.post("/logout")
def logout_user(request: LogoutRequest, db: Session = Depends(get_db)):
    """Deletes a session token from the database, logging the user out."""
    
    # 1. Find the token in the sessions table
    session_record = db.query(UserSession).filter(UserSession.token == request.token).first()
    
    # 2. If it exists, delete it
    if session_record:
        db.delete(session_record)
        db.commit()
        
    # 3. Always return a success message, even if the token was already deleted
    return {"message": "Successfully logged out"}