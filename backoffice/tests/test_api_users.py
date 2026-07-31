#!/usr/bin/env python3
"""End-to-end API tests for backoffice user management endpoints."""

import pytest
from db_models import User, UserRole, Branch
from auth import create_access_token, hash_password


# ========== MODULE SPECIFIC FIXTURES ==========

@pytest.fixture
def target_manager(db_session):
    """Creates a test user with MANAGER role for user management tests."""
    # 1. On crée d'abord une branche valide pour satisfaire la contrainte de clé étrangère
    branch = Branch(label="Branch Test Fixture")
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)

    # 2. On rattache le manager à l'ID de cette branche
    user = User(
        name="manager_test",
        password_hash=hash_password("whatever123"),
        role=UserRole.MANAGER,
        branch_id=branch.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ========== Creating User Tests (POST /users) ==========

def test_create_user_by_admin_succeeds(client, admin_token, seed_branches_data):
    """Verifies that an admin can create a new user successfully."""
    payload = {
        "name": "new_manager_user",
        "password": "securepassword123",
        "branch_id": 1,
        "role": "manager"
    }
    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "new_manager_user"
    assert data["role"] == "manager"
    assert data["is_active"] is True
    # Sécurité : vérifier que le hash ou mot de passe ne fuite pas dans la réponse
    assert "password" not in data
    assert "password_hash" not in data


def test_create_user_without_token_returns_401(client):
    """Verifies unauthenticated user creation attempts are rejected with 401."""
    payload = {
        "name": "unauth_user",
        "password": "password123",
        "branch_id": 1,
    }
    response = client.post("/users", json=payload)
    assert response.status_code == 401


def test_create_user_by_manager_returns_403(client, target_manager):
    """Verifies non-admin users (managers) cannot create users."""
    manager_token = create_access_token(user_id=target_manager.id, role=UserRole.MANAGER.value, branch_id=1)
    payload = {
        "name": "unauthorized_user",
        "password": "password123",
        "branch_id": 1,
    }
    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403


def test_create_user_duplicate_name_fails(client, admin_token, target_manager):
    """Verifies creating a user with an already existing name returns an error."""
    payload = {
        "name": target_manager.name,  # Nom déjà pris par target_manager
        "password": "anotherpassword123",
        "branch_id": 1,
    }
    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (400, 409, 422)


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
