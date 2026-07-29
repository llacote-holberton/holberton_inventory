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
from api_models import BranchOut


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
    if current_user.get("role") == 'admin' and with_managers == True:
        return crud.get_branches_with_active_managers(db)
    elif ordered_by_label:
        return crud.list_branches_ordered_by_label(db)
    else:
        return crud.list_branches(db)

