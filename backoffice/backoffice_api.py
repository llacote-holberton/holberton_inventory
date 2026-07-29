from dotenv import load_dotenv
load_dotenv()

from auth import verify_password, create_access_token
from auth import get_jwt_payload, require_manager, require_admin
from auth import require_admin_or_manager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import crud
from api_models import LoginRequest
from api_models import BranchOut, StockOut


app = FastAPI(title="Hbntory Backoffice")


# =============== AUTHENTICATION RELATED ROUTES ===============
@app.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    username = payload.username
    password = payload.password
    user = crud.get_user_by_name(db, username)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    jwt = create_access_token(user_id=user.id, role=user.role.value,
                              branch_id=user.branch_id)
    return {"access_token": jwt, "token_type": "bearer"}


@app.get("/whoami")
def whoami(current_user: dict = Depends(get_jwt_payload)):
    """Just returns the unpacked payload from JWT"""
    return current_user


# =============== USERS RELATED ROUTES ===============
from api_models import UserOut
@app.get("/users", response_model=list[UserOut])
def list_users_route(db: Session = Depends(get_db),
                     is_admin: dict = Depends(require_admin)):
    return crud.list_users(db)


@app.post("/users/{user_id}/activate")
def activate_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    success = crud.set_user_active_state(db, user_id=user_id, is_active=True)
    if not success:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"user_id": user_id, "is_active": True}


@app.post("/users/{user_id}/deactivate")
def deactivate_user_route(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    success = crud.set_user_active_state(db, user_id=user_id, is_active=False)
    if not success:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"user_id": user_id, "is_active": False}


from api_models import PasswordReset
@app.post("/users/{user_id}/reset_password")
def reset_password_route(
    user_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    from auth import hash_password

    new_hash = hash_password(payload.new_password)
    success = crud.reset_user_password(db, user_id=user_id, password_hash=new_hash)
    if not success:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"user_id": user_id, "status": "password_successfully_reset"}


from api_models import BranchAssignment
@app.post("/users/{user_id}/assign_branch")
def reassign_branch_route(
    user_id: int,
    payload: BranchAssignment,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    from sqlalchemy.exc import IntegrityError
    try:
        success = crud.assign_branch(db, user_id=user_id, branch_id=payload.branch_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid_branch_id")
    if not success:
        raise HTTPException(status_code=404, detail="user_not_found_or_not_manager")
    return {"user_id": user_id, "branch_id": payload.branch_id}


# =============== BRANCHES RELATED ROUTES ===============
@app.get("/branches", response_model=list[BranchOut])
def list_branches_route(
    # Parameter not matching 'pattern' in url (like /branches/{my_param})
    # -> FastAPI understands automatically that it must map it from
    # URL query parameters if provided (ex /branches?with_managers=true)
    ordered_by_label: bool = True,
    with_managers: bool = False,
    # Note: conversion is done through Pydantic which is somewhat flexible
    #   (ex "0" --> False, "true/false" will be understood whichever case
    #   (True, true, TRUE). Boolean also works on yes/no, t/f, on/off.
    # Failure in converting value as boolean will raise ValidationError,
    #   catched by Pydantic to trigger a 422 Response.
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_or_manager)
):
    """Uses 'combined role check' to reuse route for both roles"""
    # if current_user.get("role") == 'admin' and with_managers == True:
    #     return crud.get_branches_with_active_managers(db)
    # elif ordered_by_label:
    #     return crud.list_branches_ordered_by_label(db)
    # It is better to explicitely reject a users which tried to use
    #   an option exclusive to admins.
    if with_managers:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        return crud.get_branches_with_active_managers(db)
    if ordered_by_label:
        return crud.list_branches_ordered_by_label(db)
    return crud.list_branches(db)


# Note: putting two routes with same method to try.
# Ultimately it would probably be better to just have "one way"?
# @app.get("/branches/find/{pattern}", response_model=list[BranchOut])
@app.get("/search/branches/{pattern}", response_model=list[BranchOut])
def find_branch_by_label(
    pattern: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin_or_manager)
):
    branches = crud.find_branches_by_name(db, search_string=pattern)
    if not branches:
        raise HTTPException(status_code=404, detail="no_matching_branch_found")
    return branches


# =============== STOCKS RELATED ROUTES ===============
@app.get("/branches/{branch_id}/stocks", response_model=list[StockOut])
def get_branch_stocks_route(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_manager),
):
    """Returns the stocks for manager's OWN branch ONLY"""
    user_branch_id = current_user.get("branch_id")

    # Include "None" case for Admin and bad faith attempts.
    if user_branch_id is None or int(user_branch_id) != branch_id:
        raise HTTPException(
            status_code=403,
            detail="Trying to access another branch than yours",
        )

    return crud.list_stocks_for_branch(db, branch_id=branch_id)


# Import temporarily put here to stress relationship with route.
# Will be hoisted back to top during "code cleaning phase".
from api_models import StockAddIn
@app.post("/branches/{branch_id}/stock/add", response_model=StockOut)
def add_stock_route(
    branch_id: int,
    # Instead of plain json and manual validation in body...
    # product_id: int,
    # amount: int,
    # It's simpler and more robust to delegate to a Pydantic model
    payload: StockAddIn,
    db: Session = Depends(get_db),
    manager: dict = Depends(require_manager),
):
    m_id = manager.get("branch_id")
    # NOTE: attempt to convert m_id to int not done immediately
    #   to avoid an early 500 -> 422 Response if not convertable.
    # No need to convert branch_id either, already done by Pydantic.
    #   Only risk is value in JWT being incompatible (ex "hello")
    #   but since it comes from our own app we consider the "risk"
    #     is acceptable.
    if m_id is None or int(m_id) != branch_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden_attempt_to_affect_other_branch"
        )

    new_quantity = crud.add_stock(
        db,
        product_id=payload.product_id,
        branch_id=branch_id,
        amount=payload.amount
    )
    return {"branch_id": branch_id, "product_id": payload.product_id, "quantity": new_quantity}


from api_models import StockRemoveIn
@app.post("/branches/{branch_id}/stock/remove", response_model=StockOut)
def remove_stock_route(
    branch_id: int,
    payload: StockRemoveIn,
    db: Session = Depends(get_db),
    manager: dict = Depends(require_manager),
):
    m_id = manager.get("branch_id")
    if m_id is None or int(m_id) != branch_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden_attempt_to_affect_other_branch"
        )

    p_id = payload.product_id
    try:
        new_quantity = crud.remove_stock(
            db,
            branch_id=branch_id,
            product_id=p_id,
            amount=payload.amount
        )
    # Row exists but not enough stock to substract without going below 0.
    except crud.InsufficientStockError as exc:
        insufficient_msg = (
            f"Insufficient stock: tried to substract {payload.amount}."
            f" But only {exc.available} available!"
        )
        raise HTTPException(status_code=400, detail=insufficient_msg)
    # Row didn't exist.
    if new_quantity is None:
        nostock_msg = f"No stock found in branch {branch_id} for product {p_id}"
        raise HTTPException(status_code=404, detail=nostock_msg)
    # Everything went well.
    return {"branch_id": branch_id, "product_id": p_id, "quantity": new_quantity}



# =============== BACKOFFICE UI - Static pages ===============

# New imports for static files serving.
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
# Retrieving "true local path contextually" to cover both
#   "from host" and "in docker container" cases.
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Unique mount for everything
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Routes d'affichage des pages
@app.get("/")
@app.get("/login")
@app.get("/ui/login")
def serve_login():
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/ui/admin")
def serve_admin():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/ui/manager")
def serve_manager():
    return FileResponse(STATIC_DIR / "manager.html")
