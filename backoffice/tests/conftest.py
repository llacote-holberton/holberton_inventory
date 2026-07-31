#!/usr/bin/env python3
"""
Central pytest configuration module for backoffice and internal API tests.
Handles path resolution, in-memory SQLite setup, DB session overrides,
and shared pytest fixtures across the test suite.
"""

# ========== IMPORTS AND "INITIAL SETUP" ==========

# Ensuring pytest can find all "source files"
#   by using the required imports to "reconstruct"
#   parent path and add it to the list of paths
#   to search into (a bit like Bash PATH)
import sys
from pathlib import Path
# Add project root directory to sys.path for dynamic imports
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# == Ensuring we can use local environment variables
from os import getenv
from dotenv import load_dotenv
# Load local environment variables
load_dotenv(root_dir / ".env")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Import all models to ensure SQLAlchemy Base registers all tables before table creation
import db_models
from db_models import Base, User, UserRole, Branch
from database import get_db
from auth import create_access_token, hash_password

# Import FastAPI applications
from backoffice_api import app as backoffice_app
from internal_api import app as internal_app


# ========== "SETUP" with "in memory SQLite" to not pollute prod db ==========
# Default parameters force A NEW DATABASE for EACH connexion.
# Thus creating errors on all fixtures which expect existing table.
# engine = create_engine("sqlite:///:memory:")

# Shared in-memory SQLite database setup
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# NOTE: explicitely enabling "Enforce Foreign Keys constraints" in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
TestSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    """Yields a database session connected to the shared in-memory SQLite test database."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply database dependency overrides to both API applications
backoffice_app.dependency_overrides[get_db] = override_get_db
internal_app.dependency_overrides[get_db] = override_get_db


# ========== FIXTURES to set up tests's "contexts" ==========
# === NOTES ABOUT FIXTURES ===
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
    """Recreates all database tables before each test execution to ensure test isolation."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provides a fresh SQLAlchemy session for a test or fixture."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db(db_session):
    """Alias fixture for db_session to ensure compatibility across test modules."""
    return db_session


@pytest.fixture
def client():
    """FastAPI TestClient instance configured for the backoffice API."""
    return TestClient(backoffice_app)


@pytest.fixture
def admin_token():
    """Generates a valid JWT token with ADMIN role."""
    return create_access_token(user_id=1, role=UserRole.ADMIN.value, branch_id=None)


@pytest.fixture
def manager_token():
    """Generates a valid JWT token with MANAGER role."""
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
