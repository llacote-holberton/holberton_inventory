"""Module defining the data structure as exposed to APIs"""
# Previously called schemas.py

from pydantic import BaseModel, ConfigDict
from models import UserRole

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
