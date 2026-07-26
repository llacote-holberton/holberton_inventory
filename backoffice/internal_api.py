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

