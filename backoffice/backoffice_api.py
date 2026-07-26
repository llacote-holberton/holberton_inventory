# Required to exploit local environment variables
from dotenv import load_dotenv
load_dotenv()
# Authentication related imports
from auth import verify_password, create_access_token
from auth import get_jwt_payload, require_manager, require_admin
# CRUD operations related import
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import crud


app = FastAPI(title="Hbntory Backoffice")




# =============== AUTHENTICATION RELATED ROUTES ===============
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
    #WARNING: MUST use "user.role.value" because UserRole Enum in spite of
    #  being able to behave as a string is not correctly serialized by FastAPI.
    jwt = create_access_token(user_id=user.id, role=user.role.value,
                              branch_id=user.branch_id)
    # MUST return exactly this format to respect standard established by
    # OAuth2 (RFC 6749, section 5.1, "Access Token Response")
    return {"access_token": jwt, "token_type": "bearer"}


@app.get("/whoami")
def whoami(current_user: dict = Depends(get_jwt_payload)):
    """Just returns the unpacked payload from JWT"""
    return current_user
    # To test: 
    # curl -X POST 
    # "http://localhost:8000/login?username=god&password=<le_mdp_en_clair_du_seed>"
    # curl "http://localhost:8000/whoami" -> must get 401 because no token
    # curl "http://localhost:8000/whoami" -H "Authorization: Bearer <le_token_recupere>"


# =============== USERS RELATED ROUTES ===============
from api_models import UserOut
@app.get("/users", response_model=list[UserOut])
def list_users_route(db: Session = Depends(get_db),
                     # Requests the "depends" function to be executed
                     #   without any trouble. Name is arbitrary, could be _
                     is_admin: dict = Depends(require_admin)):
    return crud.list_users(db)  # renvoie toujours de vrais User avec le hash en mémoire...
    # ...mais FastAPI ne sérialise QUE les champs déclarés dans UserOut, le hash est ignoré


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
    # Uses a Pydantic model from api_models to automatically extract
    #   the string from JSON body
    payload: PasswordReset,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    # Exceptionally imports kept here because only used in this route.
    from auth import hash_password
    from api_models import PasswordReset

    new_hash = hash_password(payload.new_password)
    success = crud.reset_user_password(db, user_id=user_id, password_hash = new_hash)
    if not success:
        raise HTTPException(status_code = 404, detail="user_not_found")
    return {"user_id": user_id, "status": "password_successfully_reset"}

    # How to test quickly (with a valid Admin JWT)
    #   curl -X POST "http://localhost:8000/users/3/reset_password" \
    # -H "Authorization: Bearer <token_admin>" \
    # -H "Content-Type: application/json" \
    # -d '{"new_password": "nouveauMotDePasse123"}'


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
    # Branch for that id doesn't exist!
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="invalid_branch_id")
    if not success:
        raise HTTPException(status_code=404, detail="user_not_found_or_not_manager")
    return {"user_id": user_id, "branch_id": payload.branch_id}
