#!/usr/bin/env python3
"""Module exposing a REST API to manipulate Inventory database"""

# REST serveur imports
from fastapi import FastAPI, Depends, HTTPException, Header, status
# Read local environment variables
from dotenv import load_dotenv
from os import getenv
# Gets sql driver connexion to make SQL queries
from sqlalchemy.orm import Session
from database import get_db
# Gets the functions defining CRUD operations
import crud
# Pydantic models
from api_models import StockOut, ProductStockSummary

load_dotenv()
app = FastAPI(title="HbNTory Backoffice Internal API")
INTERNAL_API_KEY = getenv("INTERNAL_API_KEY")
# NOTE: Could use from fastapi.security import APIKeyHeader
# Confer Gemini discussion "Fast API - Using token based auth"

# IA-generated thanks Claude ;)
def verify_internal_key(x_api_key: str = Header(...)):
    # Not strong enough apparently.
    # if x_api_key != INTERNAL_API_KEY:
    import hmac
    if not INTERNAL_API_KEY or not hmac.compare_digest(x_api_key, INTERNAL_API_KEY):
        raise HTTPException(status_code=403, detail="forbidden")


@app.get("/internal/stock", dependencies=[Depends(verify_internal_key)])
def get_stock(product_id: int, branch_id: int, db: Session = Depends(get_db)):
    stock = crud.get_stock(db, product_id=product_id, branch_id=branch_id)
    if stock is None:
        return {"product_id": product_id, "branch_id": branch_id, "quantity": 0}
    return {"product_id": product_id, "branch_id": branch_id, "quantity": stock.quantity}


@app.get("/internal/branches/{branch_id}/stock/{product_id}",
         response_model=StockOut,
         dependencies=[Depends(verify_internal_key)]
)
def read_stock(branch_id: int, product_id: int, db: Session = Depends(get_db)):
    stock = crud.get_stock(db, product_id=product_id, branch_id=branch_id)
    if stock is None:
        return StockOut(branch_id=branch_id, product_id=product_id, quantity=0)
    # Thanks to "response_model" FastAPI will automatically convert as StockOut
    #   then as json body in Response.
    return stock


@app.get(
    "/internal/products/{product_id}/stocks",
    response_model=ProductStockSummary,
    dependencies=[Depends(verify_internal_key)]
)
def product_get_all_stocks(product_id: int, db: Session = Depends(get_db)):
    """Returns a combined object with detailed stock per branch and total"""
    # We use a prepared request dedicated to this use @FIXME IMPLEMENT IT
    product_stocks = crud.list_stocks_for_product(db, product_id=product_id)
    # Then instanciate the API model which will be automatically serialized.
    return ProductStockSummary(
        product_id=product_id,
        total_quantity = sum(stock.quantity for stock in product_stocks),
        details = product_stocks
    )



if __name__ == "__main__":
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        # Test 1: valid "request body" but auth header missing
        response = client.get(
            "/internal/stock",
            params={"product_id": 4, "branch_id": 1},
        )
        print(response.status_code)
        # Should be 15 but will be HTTP 422 because no API KEY given
        print(response.json())

        # Test 1: valid "request body" AND auth token provided.
        response_with_key = client.get(
            "/internal/stock",
            params={"product_id": 4, "branch_id": 1},
            headers={"X-API-KEY": INTERNAL_API_KEY or ""}
        )
        print("Auth passed, Status:", response_with_key.status_code)
