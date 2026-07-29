"""Module defining the data structure as exposed to APIs"""
# Previously called schemas.py

from pydantic import BaseModel, ConfigDict, Field
from db_models import UserRole

# ===== API models used for "GET" requests =====

class StockOut(BaseModel):
    """Representation of stock to serialize in Response's bodies as JSON"""
    model_config = ConfigDict(from_attributes=True)

    branch_id: int
    product_id: int
    quantity: int


class ProductStockSummary(BaseModel):
    """Wrapper to add 'total stock' on top of detail of stocks by branches"""
    product_id: int
    total_quantity: int
    details: list[StockOut]


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


class BranchOut(BaseModel):
    """Representation of stock to serialize in Response's bodies as JSON"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    # Optional, either absent or empty if not loaded. Reflects the
    #   "dynamic relationship" declared in db_models.Branch
    managers: list[UserOut] | None = None


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


class StockAddIn(BaseModel):
    """Used to validate a JSON payload put in a 'add amount request'"""
    product_id: int = Field(..., gt=0,
                            description="Target product's ID: must be >0 number")
    # Explaining syntax: each parameter of Field is a validation rule.
    # First determines what should be, if any, the default value for that field.
    # Because I put '...' which is the Python convention for "no argument"
    #   it will cause a failure immediately if request does not provide the field.
    # Second is a "strictly greater than 0" because it would make no sense
    #   starting a SQL transaction if the result would be no change.
    # Description is just equivalent of Python docstring to fill Swagger UI doc.
    amount: int = Field(..., gt=0, description="Amount to add, must be >0")
    # NOTE: the ... is mandatory for Pydantic v1, not in v2. 
    #   Kept for max compatibility.


# Same principle as above so uncommented this time. :)
class StockRemoveIn(BaseModel):
    """Used to validate a JSON payload put in a 'remove amount request'"""
    product_id: int = Field(
        ...,
        gt=0,
        description="Target product's ID: must be >0 number"
    )
    amount: int = Field(..., gt=0, description="Amount to add, must be >0")
