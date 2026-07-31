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


# ========== ADD STOCK ENDPOINT TESTS ==========

def test_add_stock_without_token_returns_401(client):
    """Verifies unauthenticated calls are rejected."""
    response = client.post(
        "/branches/1/stock/add",
        json={"product_id": 101, "amount": 10},
    )
    assert response.status_code == 401


def test_add_stock_as_admin_returns_403(client, admin_token):
    """Verifies admins cannot call manager stock endpoints."""
    response = client.post(
        "/branches/1/stock/add",
        json={"product_id": 101, "amount": 10},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403


def test_add_stock_own_branch_succeeds(client, manager_token, db_session):
    """Verifies manager can add stock to their assigned branch (branch_id=1)."""
    branch = Branch(id=1, label="Paris")
    db_session.add(branch)
    db_session.commit()

    response = client.post(
        "/branches/1/stock/add",
        json={"product_id": 101, "amount": 25},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {"branch_id": 1, "product_id": 101, "quantity": 25}

    # Verify stock row is correctly updated/inserted in database
    stock_in_db = db_session.query(Stock).filter_by(branch_id=1, product_id=101).first()
    assert stock_in_db is not None
    assert stock_in_db.quantity == 25


def test_add_stock_accumulates_existing_quantity(client, manager_token, db_session):
    """Verifies adding stock increases existing quantity properly."""
    branch = Branch(id=1, label="Paris")
    stock = Stock(branch_id=1, product_id=101, quantity=10)
    db_session.add_all([branch, stock])
    db_session.commit()

    response = client.post(
        "/branches/1/stock/add",
        json={"product_id": 101, "amount": 15},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 25


def test_add_stock_other_branch_returns_403(client, manager_token):
    """Verifies manager cannot add stock to a branch other than their assigned one."""
    response = client.post(
        "/branches/2/stock/add",
        json={"product_id": 101, "amount": 10},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden_attempt_to_affect_other_branch"


def test_add_stock_invalid_payload_returns_422(client, manager_token):
    """Verifies negative amount, zero amount, and missing fields fail Pydantic validation."""
    # Case 1: Amount <= 0
    response_negative = client.post(
        "/branches/1/stock/add",
        json={"product_id": 101, "amount": -5},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response_negative.status_code == 422

    # Case 2: Missing mandatory field ('amount')
    response_missing = client.post(
        "/branches/1/stock/add",
        json={"product_id": 101},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response_missing.status_code == 422


# ========== REMOVE STOCK ENDPOINT TESTS ==========

def test_remove_stock_without_token_returns_401(client):
    """Verifies unauthenticated requests are rejected."""
    response = client.post(
        "/branches/1/stock/remove",
        json={"product_id": 101, "amount": 5},
    )
    assert response.status_code == 401


def test_remove_stock_as_admin_returns_403(client, admin_token):
    """Verifies admins cannot call manager stock endpoints."""
    response = client.post(
        "/branches/1/stock/remove",
        json={"product_id": 101, "amount": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403


def test_remove_stock_other_branch_returns_403(client, manager_token):
    """Verifies manager cannot remove stock from a branch other than their assigned one."""
    response = client.post(
        "/branches/2/stock/remove",
        json={"product_id": 101, "amount": 5},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden_attempt_to_affect_other_branch"


def test_remove_stock_success(client, manager_token, db_session):
    """Verifies successful stock removal updates database and returns remaining quantity."""
    branch = Branch(id=1, label="Paris")
    stock = Stock(branch_id=1, product_id=101, quantity=20)
    db_session.add_all([branch, stock])
    db_session.commit()

    response = client.post(
        "/branches/1/stock/remove",
        json={"product_id": 101, "amount": 5},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"branch_id": 1, "product_id": 101, "quantity": 15}

    # Verify database record updated
    stock_in_db = db_session.query(Stock).filter_by(branch_id=1, product_id=101).first()
    assert stock_in_db.quantity == 15


def test_remove_stock_nonexistent_returns_404(client, manager_token, db_session):
    """Verifies 404 error when attempting to remove stock for a non-existent row."""
    branch = Branch(id=1, label="Paris")
    db_session.add(branch)
    db_session.commit()

    response = client.post(
        "/branches/1/stock/remove",
        json={"product_id": 999, "amount": 5},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No stock found in branch 1 for product 999"


def test_remove_stock_insufficient_returns_400(client, manager_token, db_session):
    """Verifies 400 Bad Request with custom detail when requested amount > stock available."""
    branch = Branch(id=1, label="Paris")
    stock = Stock(branch_id=1, product_id=101, quantity=3)
    db_session.add_all([branch, stock])
    db_session.commit()

    response = client.post(
        "/branches/1/stock/remove",
        json={"product_id": 101, "amount": 10},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert response.status_code == 400
    # Check that exception message is formatted as expected
    assert "Insufficient stock" in response.json()["detail"]
    assert "3 available" in response.json()["detail"]

    # Verify stock in DB was NOT changed
    stock_in_db = db_session.query(Stock).filter_by(branch_id=1, product_id=101).first()
    assert stock_in_db.quantity == 3


def test_remove_stock_invalid_payload_returns_422(client, manager_token):
    """Verifies Pydantic rejection for invalid values (amount <= 0, product_id <= 0, missing payload)."""
    # Case 1: Amount <= 0
    response_amount = client.post(
        "/branches/1/stock/remove",
        json={"product_id": 101, "amount": 0},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response_amount.status_code == 422

    # Case 2: Product ID <= 0
    response_prod = client.post(
        "/branches/1/stock/remove",
        json={"product_id": -1, "amount": 5},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response_prod.status_code == 422

    # Case 3: Missing mandatory field
    response_missing = client.post(
        "/branches/1/stock/remove",
        json={"amount": 5},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response_missing.status_code == 422
