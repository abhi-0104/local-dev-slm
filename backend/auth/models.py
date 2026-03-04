from pydantic import BaseModel

# --- REQUEST SCHEMAS (Data coming IN from the user) ---

class UserLogin(BaseModel):
    """The exact shape of data we expect when someone tries to log in."""
    username: str
    password: str

class UserCreate(BaseModel):
    """The shape of data we expect when an IT Admin creates a new employee."""
    username: str
    password: str
    role: str = "employee"

# --- RESPONSE SCHEMAS (Data going OUT to the user) ---

class TokenResponse(BaseModel):
    """The shape of data we send back after a successful login."""
    access_token: str
    token_type: str = "bearer"

class LogoutRequest(BaseModel):
    """The shape of data we expect when a user logs out."""
    token: str