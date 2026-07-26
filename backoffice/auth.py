"""Module exposing hashing functions to manage user passwords
   For now using bcrypt for simplicity and speed, will maybe
   change for Argon2Id later if it's not too hard.
"""
import bcrypt

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


# Self-teaching notes
# The hash would generate something like this after UTF-8 decoding...
# $2b$12$KIXQx5Z8vN3mR7wYtL9pOeJhX2Wn4Fk6Ds8Tq1Vr0Cy5Ab3Ez.Wm
# This is the concatenation of several things, each field is separated by '$'.
# * Bcrypt version used to hash
# * Cost factor (higher means more effort to crack from brute-force)
# * salt used (22 chars)
# * actual password's hash made with that salt
