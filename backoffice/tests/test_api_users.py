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
from db_models import Base, User, UserRole
from database import get_db
from auth import create_access_token, hash_password
from backoffice_api import app  # adapte selon le nom réel de ton fichier back.py


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

# Fixtures are small bits of code used to prepare what is needed to set a
# "state" relevant to the test to assert.
# Pytest knows which fixture(s) to use in tests by...
# * Auto-discovering every file named test_* (note: current filename means
#   must be executed explicitely with pytest tests/tests_api_users.py -v
# * Getting every function decorated with @pytest.fixture to set a registry.
# * Analyzing the signature of all functions named with test_ as prefix
#   and matching fixtures based on names.
# IMPORTANT: to share fixtures across several test files
#   (ex test_api_users, test_api_stocks) one can define "shared fixtures" in
#   a specifically named 'conftest.py' file to place "as sibling or parent" of
#   all files which may require it.

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
def target_manager(db_session):
    """Creates an actual test user with role 'manager' for all subsequent tests"""
    user = User(
        name="manager_test",
        password_hash=hash_password("whatever123"),
        role=UserRole.MANAGER,
        branch_id=1,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ========== Activating / Deactivating User Tests ==========

def test_deactivate_existing_user_succeeds(admin_token, target_manager):
    response = client.post(
        f"/users/{target_manager.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_existing_user_succeeds(admin_token, target_manager, db_session):
    # on désactive d'abord pour vérifier une vraie transition d'état
    target_manager.is_active = False
    db_session.commit()

    response = client.post(
        f"/users/{target_manager.id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_deactivate_nonexistent_user_returns_404(admin_token):
    response = client.post(
        "/users/9999/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


def test_deactivate_without_token_returns_401(target_manager):
    response = client.post(f"/users/{target_manager.id}/deactivate")
    assert response.status_code == 401


def test_deactivate_without_admin_role_returns_403(target_manager):
    manager_token = create_access_token(user_id=2, role=UserRole.MANAGER.value, branch_id=1)
    response = client.post(
        f"/users/{target_manager.id}/deactivate",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
