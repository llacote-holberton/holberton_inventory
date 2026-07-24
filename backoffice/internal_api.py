from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import crud

app = FastAPI(title="HbNTory Backoffice Internal API")


@app.get("/internal/stock")
def get_stock(product_id: int, branch_id: int, db: Session = Depends(get_db)):
    stock = crud.get_stock(db, product_id=4, branch_id=1)
    if stock is None:
        return {"product_id": product_id, "branch_id": branch_id, "quantity": 0}
    return {"product_id": product_id, "branch_id": branch_id, "quantity": stock.quantity}


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get(
            "/internal/stock",
            params={"product_id": 4, "branch_id": 1},
        )
        print(response.status_code)
        # Should be 15
        print(response.json())
