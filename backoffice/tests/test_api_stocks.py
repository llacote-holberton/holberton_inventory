#!/usr/bin/env python3
"""End-to-end API tests for backoffice stock management endpoints."""

import pytest
from db_models import Branch, Stock


# ========== MODULE SPECIFIC FIXTURES ==========

@pytest.fixture
def seed_stock_data(db_session):
    """Populates database with sample branches and stock records for testing."""
    # Note: ID 1 matches the branch_id encoded in the shared manager_token fixture
    paris = Branch(id=1, label="Paris")
    bordeaux = Branch(id=2, label="Bordeaux")
    db_session.add_all([paris, bordeaux])
    db_session.commit()

    stock_paris_1 = Stock(branch_id=paris.id, product_id=101, quantity=50)
    stock_paris_2 = Stock(branch_id=paris.id, product_id=102, quantity=100)
    stock_bordeaux_1 = Stock(branch_id=bordeaux.id, product_id=101, quantity=30)

    db_session.add_all([stock_paris_1, stock_paris_2, stock_bordeaux_1])
    db_session.commit()

    return {
        "paris": paris,
        "bordeaux": bordeaux,
        "paris_stocks": [stock_paris_1, stock_paris_2],
        "bordeaux_stocks": [stock_bordeaux_1],
    }


# ========== AUTHENTICATION AND AUTHORIZATION TESTS ==========

def test_get_branch_stocks_without_token_returns_401(client):
    """Verifies unauthenticated access to branch stocks is rejected."""
    response = client.get("/branches/1/stocks")
    assert response.status_code == 401


def test_get_branch_stocks_with_invalid_token_returns_401(client):
    """Verifies requests with malformed or invalid tokens are rejected."""
    response = client.get(
        "/branches/1/stocks",
        headers={"Authorization": "Bearer invalid_token_xyz"}
    )
    assert response.status_code == 401


def test_get_branch_stocks_as_admin_returns_403(client, admin_token, seed_stock_data):
    """Verifies Admin users cannot access branch stocks (strict manager-only restriction)."""
    paris_id = seed_stock_data["paris"].id
    response = client.get(
        f"/branches/{paris_id}/stocks",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403


# ========== BRANCH ACCESS PERMISSION TESTS ==========

def test_get_branch_stocks_own_branch_succeeds(client, manager_token, seed_stock_data):
    """Verifies manager can successfully retrieve stocks for their assigned branch (branch_id=1)."""
    paris_id = seed_stock_data["paris"].id
    response = client.get(
        f"/branches/{paris_id}/stocks",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    product_ids = {item["product_id"] for item in data}
    assert product_ids == {101, 102}


def test_get_branch_stocks_other_branch_returns_403(client, manager_token, seed_stock_data):
    """Verifies manager cannot access stocks of a branch other than their own."""
    bordeaux_id = seed_stock_data["bordeaux"].id
    response = client.get(
        f"/branches/{bordeaux_id}/stocks",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Trying to access another branch than yours"


def test_get_branch_stocks_empty_when_no_records(client, manager_token, db_session):
    """Verifies endpoint returns 200 with an empty list when manager's branch has no stock items."""
    paris = Branch(id=1, label="Paris")
    db_session.add(paris)
    db_session.commit()

    response = client.get(
        "/branches/1/stocks",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_branch_stocks_invalid_branch_id_param_returns_422(client, manager_token):
    """Verifies non-integer branch_id parameter returns 422 validation error."""
    response = client.get(
        "/branches/invalid_id/stocks",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 422
