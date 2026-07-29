#!/usr/bin/env python3

# ========== IMPORTS AND "INITIAL SETUP" ==========
# REQUIRED to reconstruct dynamically the path to parent folder in which
#   the models are located.
import sys
from pathlib import Path
# Adds the parent of current folder to the list of paths
#   to parse when looking for modules (a bit like bash PATH)
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# REQUIRED to exploit "local environment variables"
from os import getenv
from dotenv import load_dotenv
load_dotenv()

# TESTS related imports.
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from db_models import Base, User, UserRole, Branch
from database import get_db
from auth import create_access_token, hash_password
from backoffice_api import app


# ========== "SETUP" with "in memory SQLite" to not pollute prod db ==========
# Default parameters force A NEW DATABASE for EACH connexion.
# Thus creating errors on all fixtures which expect existing table.
# engine = create_engine("sqlite:///:memory:")
engine = create_engine(
    "sqlite:///:memory:",
    # Required to allow other py threads to use the same connexion
    #  in addition to the next argument (also necessary)
    connect_args={"check_same_thread": False},
    # Ensures there is only ONE connexion for the whole engine so same database
    #   for all fixtures.
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ========== FIXTURES SETUP ==========
@pytest.fixture(autouse=True)
def setup_database():
    """Recreates database tables to realize tests from a fresh state"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    """Generates a new local db connexion"""
    db = TestSessionLocal()
    yield db
    db.close()


@pytest.fixture
def admin_token():
    """Directly creates an 'admin-level' token to simulate authenticated admin."""
    return create_access_token(user_id=1, role=UserRole.ADMIN.value, branch_id=None)


@pytest.fixture
def manager_token():
    """Directly creates a 'manager-level' token to simulate authenticated manager."""
    return create_access_token(user_id=2, role=UserRole.MANAGER.value, branch_id=1)


@pytest.fixture
def seed_branches_data(db_session):
    """Populates database with sample branches and active/inactive managers."""
    paris = Branch(label="Paris")
    bordeaux = Branch(label="Bordeaux")
    bourges = Branch(label="Bourges")
    
    db_session.add_all([paris, bordeaux, bourges])
    db_session.commit()
    db_session.refresh(paris)
    db_session.refresh(bordeaux)
    db_session.refresh(bourges)

    manager_active = User(
        name="active_manager_paris",
        password_hash=hash_password("pwd123456"),
        role=UserRole.MANAGER,
        branch_id=paris.id,
        is_active=True,
    )
    manager_inactive = User(
        name="inactive_manager_paris",
        password_hash=hash_password("pwd123456"),
        role=UserRole.MANAGER,
        branch_id=paris.id,
        is_active=False,
    )
    db_session.add_all([manager_active, manager_inactive])
    db_session.commit()

    return {"paris": paris, "bordeaux": bordeaux, "bourges": bourges}


# ========== AUTHENTICATION AND AUTHORIZATION TESTS ==========

def test_list_branches_without_token_returns_401():
    response = client.get("/branches")
    assert response.status_code == 401


def test_list_branches_with_invalid_token_returns_401():
    response = client.get("/branches", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert response.status_code == 401


def test_list_branches_with_manager_token_succeeds(manager_token, seed_branches_data):
    response = client.get(
        "/branches",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_list_branches_with_admin_token_succeeds(admin_token, seed_branches_data):
    response = client.get(
        "/branches",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


# ========== QUERY PARAMETERS AND ORDERING TESTS ==========

def test_list_branches_ordered_by_label_default(manager_token, seed_branches_data):
    response = client.get(
        "/branches",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    labels = [b["label"] for b in response.json()]
    assert labels == ["Bordeaux", "Bourges", "Paris"]


def test_list_branches_unordered_or_default_id(manager_token, seed_branches_data):
    response = client.get(
        "/branches?ordered_by_label=false",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    labels = [b["label"] for b in response.json()]
    assert labels == ["Paris", "Bordeaux", "Bourges"]


def test_list_branches_invalid_boolean_param_returns_422(manager_token):
    response = client.get(
        "/branches?ordered_by_label=invalid_bool_value",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 422


# ========== WITH_MANAGERS PARAMETER AND PERMISSIONS TESTS ==========

def test_list_branches_with_managers_as_admin_succeeds(admin_token, seed_branches_data):
    response = client.get(
        "/branches?with_managers=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    
    paris_branch = next(b for b in data if b["label"] == "Paris")
    assert "managers" in paris_branch
    assert paris_branch["managers"] is not None
    assert len(paris_branch["managers"]) == 1
    assert paris_branch["managers"][0]["name"] == "active_manager_paris"


def test_list_branches_with_managers_as_manager_returns_403(manager_token, seed_branches_data):
    response = client.get(
        "/branches?with_managers=true",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_list_branches_with_managers_false_as_manager_succeeds(manager_token, seed_branches_data):
    response = client.get(
        "/branches?with_managers=false",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
