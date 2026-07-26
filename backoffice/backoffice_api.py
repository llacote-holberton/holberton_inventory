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


from auth import verify_password
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_name(db, username)
    # NOTE: it's a "best practice" in security to NOT detail WHY login failed.
    #   as telling "wrong password" (implied: good login) for example would
    #   give valuable information to attackers.
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    # Password checks out we can generate a Json Web Token (JWT)
    #   which can be stored in user's browser to be reused automagically later
    #   when user will make requests to interact with database.
    #FIXME replace with JWT generation
    return {"msg": "Yay! Your password has been successfully validated!"}

# @app.post("/branches/{branch_id}/stock/add")
# def add_stock_route(
#     branch_id: int,
#     product_id: int,
#     amount: int,
#     db: Session = Depends(get_db),
# ):
#     new_quantity = crud.add_stock(db, product_id=product_id, branch_id=branch_id, amount=amount)
#     return {"branch_id": branch_id, "product_id": product_id, "quantity": new_quantity}
