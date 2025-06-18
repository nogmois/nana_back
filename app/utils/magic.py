# app/utils/magic.py
import secrets, jwt
from datetime import datetime, timedelta
from config.settings import JWT_SECRET, JWT_ALGORITHM

def generate_magic_token() -> str:
    return secrets.token_urlsafe(32)

def jwt_for_user(email: str, role: str = "parent"):
    payload = {
        "sub": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=3),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
