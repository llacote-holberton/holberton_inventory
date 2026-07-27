"""Module defining the data structure as exposed to APIs"""
# Previously called schemas.py

from pydantic import BaseModel, ConfigDict, Field

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


class BranchOut(BaseModel):
    """Representation of stock to serialize in Response's bodies as JSON"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
