import bcrypt
import secrets
import hashlib
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import User, UserSession

def get_password_hash(password: str) -> str:
    """Converts a plain text password into a secure bcrypt hash string."""
    # 1. Bcrypt requires 'bytes' not standard strings, so we encode it
    pwd_bytes = password.encode('utf-8')
    # 2. Generate a random 'salt' (extra random characters added for security)
    salt = bcrypt.gensalt()
    # 3. Hash the password with the salt
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # 4. Decode it back to a standard string so we can save it in SQLite easily
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the provided password matches the hash in the database."""
    # Convert both strings back into bytes for comparison
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # bcrypt securely compares them
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def create_session_token() -> str:
    """Generates a secure, random 64-character string to act as a session token."""
    return secrets.token_hex(32)

def hash_token(token: str) -> str:
    """Hashes a session token using SHA-256 for secure database storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

# This tells FastAPI to look for a "Bearer" token in the web request headers
security_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """The Security Guard: Checks the token and returns the logged-in user."""
    
    # 1. Grab the token string from the request and hash it
    token = credentials.credentials
    hashed = hash_token(token)
    
    # 2. Look up the token in our database
    session_record = db.query(UserSession).filter(UserSession.token == hashed).first()
    
    # 3. If it doesn't exist, kick them out
    if not session_record:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
        
    # 4. If it does exist, find the User it belongs to
    user = db.query(User).filter(User.id == session_record.user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
        
    # 5. Let them in! Hand the user data to the next step.
    return user