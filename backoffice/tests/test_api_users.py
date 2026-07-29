#!/usr/bin/env python3
"""End-to-end API tests for backoffice user management endpoints."""

import pytest
from db_models import User, UserRole
from auth import create_access_token, hash_password


# ========== MODULE SPECIFIC FIXTURES ==========

@pytest.fixture
def target_manager(db_session):
    """Creates a test user with MANAGER role for user management tests."""
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

def test_deactivate_existing_user_succeeds(client, admin_token, target_manager):
    response = client.post(
        f"/users/{target_manager.id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_existing_user_succeeds(client, admin_token, target_manager, db_session):
    target_manager.is_active = False
    db_session.commit()

    response = client.post(
        f"/users/{target_manager.id}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_deactivate_nonexistent_user_returns_404(client, admin_token):
    response = client.post(
        "/users/9999/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


def test_deactivate_without_token_returns_401(client, target_manager):
    response = client.post(f"/users/{target_manager.id}/deactivate")
    assert response.status_code == 401


def test_deactivate_without_admin_role_returns_403(client, target_manager):
    manager_token = create_access_token(user_id=2, role=UserRole.MANAGER.value, branch_id=1)
    response = client.post(
        f"/users/{target_manager.id}/deactivate",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
