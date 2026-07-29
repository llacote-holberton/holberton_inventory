#!/usr/bin/env python3
"""Unit tests for user CRUD database operations."""

import pytest
from sqlalchemy.exc import IntegrityError
from db_models import UserRole, Branch
from crud import (
    create_user,
    get_user_by_name,
    list_users,
    reset_user_password,
    assign_branch,
    set_user_active_state,
)


# ========== FIXTURES ==========

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

    success = reset_user_password(db, user_id=user.id, password_hash="new_hash")
    db.refresh(user)

    assert success is True
    assert user.password_hash == "new_hash"

    failed = reset_user_password(db, user_id=9999, password_hash="any_hash")
    assert failed is False


def test_assign_branch_manager_only(db, sample_branch):
    """Verifies that branch assignment works ONLY for Managers (business rule)."""
    manager = create_user(db, user_name="mgr", pwd_hash="hash", role=UserRole.MANAGER)
    admin = create_user(db, user_name="adm", pwd_hash="hash", role=UserRole.ADMIN)

    success_mgr = assign_branch(db, user_id=manager.id, branch_id=sample_branch.id)
    db.refresh(manager)
    assert success_mgr is True
    assert manager.branch_id == sample_branch.id

    success_adm = assign_branch(db, user_id=admin.id, branch_id=sample_branch.id)
    db.refresh(admin)
    assert success_adm is False
    assert admin.branch_id is None


def test_unassign_branch_from_manager(db, sample_branch):
    """Verifies passing branch_id=None removes branch assignment from manager."""
    manager = create_user(db, user_name="mgr_unassign", pwd_hash="hash", branch_id=sample_branch.id)
    assert manager.branch_id == sample_branch.id

    success = assign_branch(db, user_id=manager.id, branch_id=None)
    db.refresh(manager)

    assert success is True
    assert manager.branch_id is None


def test_assign_branch_non_existent_user_returns_false(db, sample_branch):
    """Verifies assign_branch returns False for unknown user_id."""
    result = assign_branch(db, user_id=9999, branch_id=sample_branch.id)
    assert result is False


def test_set_user_active_state(db):
    """Verifies toggling user active/inactive state."""
    user = create_user(db, user_name="eva", pwd_hash="hash")
    assert user.is_active is True

    set_user_active_state(db, user_id=user.id, is_active=False)
    db.refresh(user)
    assert user.is_active is False

    set_user_active_state(db, user_id=user.id, is_active=True)
    db.refresh(user)
    assert user.is_active is True

    result = set_user_active_state(db, user_id=9999, is_active=False)
    assert result is False
