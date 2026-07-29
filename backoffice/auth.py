"""Module exposing hashing functions to manage user passwords"""

from datetime import datetime, timedelta, timezone
from os import getenv
import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt

load_dotenv()

JWT_SECRET = getenv("JWT_SECRET")
JWT_ALGORITHM = getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(getenv("JWT_EXPIRE_MINUTES", 60))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ========== USER PASSWORD MANAGEMENT METHODS ==========
def hash_password(plain_password: str) -> str:
    """Generates a long string by applying a 'random salt' then hashing."""
    hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Uses built-in library function to verify a plain password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ========== JSON WEB TOKEN MANAGEMENT METHODS ==========
def create_access_token(*, user_id: int, role: str, branch_id: int | None) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "branch_id": branch_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_jwt_payload(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token_expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid_token")


# ========== VALIDATION METHODS BASED ON ANALYZING JWT ==========
def require_manager(current_user: dict = Depends(get_jwt_payload)) -> dict:
    if current_user.get("role") != "manager":
        raise HTTPException(status_code=403, detail="forbidden")
    return current_user


def require_admin(current_user: dict = Depends(get_jwt_payload)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return current_user


def require_admin_or_manager(current_user: dict = Depends(get_jwt_payload)) -> dict:
    if current_user.get("role") not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="forbidden")
    return current_user
