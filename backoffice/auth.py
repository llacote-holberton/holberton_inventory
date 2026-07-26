"""Module exposing hashing functions to manage user passwords
   For now using bcrypt for simplicity and speed, will maybe
   change for Argon2Id later if it's not too hard.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from os import getenv
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer


load_dotenv()

JWT_SECRET = getenv("JWT_SECRET")
JWT_ALGORITHM = getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(getenv("JWT_EXPIRE_MINUTES", 60))
# Using a class which knows how to extract JWT from request headers
# The tokenUrl is given so Swagger interface can auto-document where
#   to call to generate a token and "make it for user" using "try".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def hash_password(plain_password: str) -> str:
    """Generates a long string by applying a 'random salt' then hashing."""
    hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    # Hashing function returns bytes so we need to "decode as string" for storage
    return hashed_bytes.decode("utf-8")
    # Would generated s


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Uses built-in library function to."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(*, user_id: int, role: str,
                        branch_id: int | None) -> str:
    payload = {
        # Note: "sub" is the mandatory, arbitrary field to hold the "identifier"
        "sub": str(user_id),
        "role": role,
        "branch_id": branch_id,
        # Note: exp is special field used to check expiration cf comment.
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Note: Claude suggested get_current_user as a conventional name
#   but I found it counter-intuitive considering we never actually
#   "get" a "User" (aka data from db), we just exploit whatever data
#   we put in the jwt when creating it. Hence why having the "role" value
#     in it is mandatory here. And also creates a limit.
# If a user is deactivated while having a valid JWT, (s)he will be
#   able to connect until its current jwt expires.
def get_jwt_payload(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token_expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid_token")


def require_manager(current_user: dict = Depends(get_jwt_payload)) -> dict:
    if current_user.get("role") != "manager":
        raise HTTPException(status_code=403, detail="forbidden")
    return current_user


def require_admin(current_user: dict = Depends(get_jwt_payload)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return current_user


# ====== SELF-TEACHING NOTES ======
# == On user password hashing with bcrypt ==
# The hash would generate something like this after UTF-8 decoding...
# $2b$12$KIXQx5Z8vN3mR7wYtL9pOeJhX2Wn4Fk6Ds8Tq1Vr0Cy5Ab3Ez.Wm
# This is the concatenation of several things, each field is separated by '$'.
# * Bcrypt version used to hash
# * Cost factor (higher means more effort to crack from brute-force)
# * salt used (22 chars)
# * actual password's hash made with that salt
# == On JWT generation ==
# the "exp" key in payload is a special field known by the pyjwt library
#   so that when the token is read the date is automatically decoded and
#   checked against current time, raising an Exception if expired.
