#!/usr/bin/env python3
"""Module exposing a REST API to manipulate Inventory database"""

import hmac
from os import getenv
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from database import get_db
import crud
from api_models import StockOut, ProductStockSummary, BranchOut

load_dotenv()
app = FastAPI(title="HbNTory Backoffice Internal API")
INTERNAL_API_KEY = getenv("INTERNAL_API_KEY")


def verify_internal_key(x_api_key: str = Header(...)):
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
    return stock


@app.get(
    "/internal/products/{product_id}/stocks",
    response_model=ProductStockSummary,
    dependencies=[Depends(verify_internal_key)]
)
def product_get_all_stocks(product_id: int, db: Session = Depends(get_db)):
    """Returns a combined object with detailed stock per branch and total"""
    product_stocks = crud.list_stocks_for_product(db, product_id=product_id)
    return ProductStockSummary(
        product_id=product_id,
        total_quantity=sum(stock.quantity for stock in product_stocks),
        details=product_stocks
    )


@app.get("/internal/branches/{branch_id}/stocks",
         response_model=list[StockOut],
         dependencies=[Depends(verify_internal_key)]
)
def branch_get_all_stocks(branch_id: int, db: Session = Depends(get_db)):
    return crud.list_stocks_for_branch(db, branch_id=branch_id)


@app.get("/internal/branches/list",
         response_model=list[BranchOut],
         dependencies=[Depends(verify_internal_key)]
)
def list_branches_route(db: Session = Depends(get_db)):
    return crud.list_branches(db)


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get(
            "/internal/stock",
            params={"product_id": 4, "branch_id": 1},
        )
        print(response.status_code)
        print(response.json())

        response_with_key = client.get(
            "/internal/stock",
            params={"product_id": 4, "branch_id": 1},
            headers={"X-API-KEY": INTERNAL_API_KEY or ""}
        )
        print("Auth passed, Status:", response_with_key.status_code)
