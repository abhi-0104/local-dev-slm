import bcrypt
import secrets

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