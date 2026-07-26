"""Module defining the data structure as exposed to APIs"""
# Previously called schemas.py

from pydantic import BaseModel, ConfigDict, Field
from db_models import UserRole

class UserOut(BaseModel):
    """UserOut as in user outputed for API consumption"""

    # "Helper class" mapping automatically this class attributes
    #    to ones defined in a ORM Model defined from SQLAlchemy library.
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: UserRole
    branch_id: int | None
    is_active: bool
    # Password_hash is left out on purpose for security reasons.


# ===== API models used for "POST" requests =====

class LoginRequest(BaseModel):
    username: str
    password: str


class PasswordReset(BaseModel):
    """Just a Data Transfert Object to ease up new password retrieval"""
    # new_password: str  # Not secure enough to my taste (would accept "")
    new_password: str = Field(min_length=8, max_length=72)
    # Max_length because for now we use bcrypt
    # Field is a class allowing to specify data validation constraints
    #   upon the data type.


class BranchAssignment(BaseModel):
    branch_id: int = Field(gt=0)
