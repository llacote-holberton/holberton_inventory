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

# ========== DEPENDENCIES & SETUP ==========
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from db_models import Base, User, UserRole, Branch
from crud import (
    create_user,
    get_user_by_name,
    list_users,
    reset_user_password,
    assign_branch,
    set_user_active_state,
)

# SQLite in-memory setup for isolated fast tests
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine)


# ========== FIXTURES ==========
@pytest.fixture(autouse=True)
def setup_database():
    """Recreates all database tables before each test and drops them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Provides a fresh database session for a single test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_branch(db):
    """Fixture creating a branch for tests that require a valid branch_id."""
    branch = Branch(label="Toulouse Test")
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


# ========== USER CRUD TESTS ==========

def test_create_user_success(db):
    """Verifies that a user can be created with default values (Manager, Active)."""
    user = create_user(
        db,
        user_name="alice",
        pwd_hash="hashed_secret_123"
    )

    assert user.id is not None
    assert user.name == "alice"
    assert user.password_hash == "hashed_secret_123"
    assert user.role == UserRole.MANAGER
    assert user.is_active is True
    assert user.branch_id is None


def test_create_user_with_admin_role_and_branch(db, sample_branch):
    """Verifies creating an admin user assigned to a branch."""
    admin = create_user(
        db,
        user_name="admin_bob",
        pwd_hash="admin_hash",
        role=UserRole.ADMIN,
        branch_id=sample_branch.id
    )

    assert admin.id is not None
    assert admin.role == UserRole.ADMIN
    assert admin.branch_id == sample_branch.id


def test_create_user_duplicate_name_raises_integrity_error(db):
    """Verifies that creating two users with the same name fails (unique constraint)."""
    create_user(db, user_name="unique_user", pwd_hash="hash1")

    with pytest.raises(IntegrityError):
        create_user(db, user_name="unique_user", pwd_hash="hash2")


def test_get_user_by_name(db):
    """Verifies retrieving a user by name, and returning None if non-existent."""
    create_user(db, user_name="charlie", pwd_hash="hash_charlie")

    found_user = get_user_by_name(db, "charlie")
    missing_user = get_user_by_name(db, "unknown_user")

    assert found_user is not None
    assert found_user.name == "charlie"
    assert missing_user is None


def test_list_users(db):
    """Verifies listing all users ordered by ID and role."""
    create_user(db, user_name="user1", pwd_hash="hash1", role=UserRole.MANAGER)
    create_user(db, user_name="user2", pwd_hash="hash2", role=UserRole.ADMIN)

    users = list_users(db)

    assert len(users) == 2
    assert [u.name for u in users] == ["user1", "user2"]


def test_reset_user_password(db):
    """Verifies password reset on existing vs non-existing user."""
    user = create_user(db, user_name="david", pwd_hash="old_hash")

    # Success case
    success = reset_user_password(db, user_id=user.id, password_hash="new_hash")
    db.refresh(user)

    assert success is True
    assert user.password_hash == "new_hash"

    # Non-existing user ID
    failed = reset_user_password(db, user_id=9999, password_hash="any_hash")
    assert failed is False


def test_assign_branch_manager_only(db, sample_branch):
    """Verifies that branch assignment works ONLY for Managers (business rule)."""
    manager = create_user(db, user_name="mgr", pwd_hash="hash", role=UserRole.MANAGER)
    admin = create_user(db, user_name="adm", pwd_hash="hash", role=UserRole.ADMIN)

    # Must succeed for Manager
    success_mgr = assign_branch(db, user_id=manager.id, branch_id=sample_branch.id)
    db.refresh(manager)
    assert success_mgr is True
    assert manager.branch_id == sample_branch.id

    # Must fail (return False) for Admin
    success_adm = assign_branch(db, user_id=admin.id, branch_id=sample_branch.id)
    db.refresh(admin)
    assert success_adm is False
    assert admin.branch_id is None


def test_set_user_active_state(db):
    """Verifies toggling user active/inactive state."""
    user = create_user(db, user_name="eva", pwd_hash="hash")
    assert user.is_active is True

    # Deactivate
    set_user_active_state(db, user_id=user.id, is_active=False)
    db.refresh(user)
    assert user.is_active is False

    # Reactivate
    set_user_active_state(db, user_id=user.id, is_active=True)
    db.refresh(user)
    assert user.is_active is True

    # Unknown user
    result = set_user_active_state(db, user_id=9999, is_active=False)
    assert result is False
