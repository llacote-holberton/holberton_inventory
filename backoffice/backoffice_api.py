from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
import crud

app = FastAPI(title="Hbntory Backoffice")

from api_models import UserOut
@app.get("/users", response_model=list[UserOut])
def list_users_route(db: Session = Depends(get_db)):
    return crud.list_users(db)  # renvoie toujours de vrais User avec le hash en mémoire...
    # ...mais FastAPI ne sérialise QUE les champs déclarés dans UserOut, le hash est ignoré




# @app.post("/branches/{branch_id}/stock/add")
# def add_stock_route(
#     branch_id: int,
#     product_id: int,
#     amount: int,
#     db: Session = Depends(get_db),
# ):
#     new_quantity = crud.add_stock(db, product_id=product_id, branch_id=branch_id, amount=amount)
#     return {"branch_id": branch_id, "product_id": product_id, "quantity": new_quantity}
