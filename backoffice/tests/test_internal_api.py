#!/usr/bin/env python3
"""Test module dedicated to asserting endpoints of Internal API used by AI services."""

import pytest
from fastapi.testclient import TestClient
from db_models import Branch, Stock
from internal_api import app as internal_app

# "INTERNAL_API_KEY" override configuration for tests
TEST_API_KEY = "cle-de-test-super-securisee"
VALID_HEADERS = {"x-api-key": TEST_API_KEY}
internal_client = TestClient(internal_app)


@pytest.fixture(autouse=True)
def override_api_key(monkeypatch):
    monkeypatch.setattr("internal_api.INTERNAL_API_KEY", TEST_API_KEY)


@pytest.fixture
def two_branches(db_session):
    esquirol = Branch(id=1, label="Toulouse Esquirol")
    caussade = Branch(id=4, label="Caussade")
    db_session.add_all([esquirol, caussade])
    db_session.commit()
    return esquirol, caussade


@pytest.fixture
def stock_data(db_session, two_branches):
    """Product ID 6 present in two branches with different stock quantities."""
    db_session.add_all([
        Stock(branch_id=1, product_id=6, quantity=15),
        Stock(branch_id=4, product_id=6, quantity=55),
        Stock(branch_id=4, product_id=2, quantity=777),
    ])
    db_session.commit()


# ---- GET /internal/branches/{branch_id}/stock/{product_id} ----

def test_get_stock_existing_line_returns_quantity(stock_data):
    response = internal_client.get("/internal/branches/4/stock/6", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"branch_id": 4, "product_id": 6, "quantity": 55}


def test_get_stock_missing_line_returns_zero_not_404(two_branches):
    response = internal_client.get("/internal/branches/1/stock/999", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json()["quantity"] == 0


def test_get_stock_without_api_key_returns_error(stock_data):
    response = internal_client.get("/internal/branches/4/stock/6")
    assert response.status_code in (401, 403, 422)


def test_get_stock_with_wrong_api_key_returns_error(stock_data):
    response = internal_client.get(
        "/internal/branches/4/stock/6",
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code in (401, 403)


# ---- GET /internal/products/{product_id}/stocks ----

def test_stock_by_product_across_branches(stock_data):
    response = internal_client.get("/internal/products/6/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    result = response.json()
    assert result["product_id"] == 6
    assert result["total_quantity"] == 70  # 15 + 55
    assert len(result["details"]) == 2
    branch_ids = {entry["branch_id"] for entry in result["details"]}
    assert branch_ids == {1, 4}


def test_stock_by_product_with_no_stock_returns_empty_summary(two_branches):
    response = internal_client.get("/internal/products/999/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    result = response.json()
    assert result["product_id"] == 999
    assert result["total_quantity"] == 0
    assert result["details"] == []


# ---- GET /internal/branches/{branch_id}/stock ----

def test_stock_by_branch_lists_all_products(stock_data):
    response = internal_client.get("/internal/branches/4/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    product_ids = {r["product_id"] for r in results}
    assert product_ids == {6, 2}


def test_stock_by_branch_with_no_stock_returns_empty_list(two_branches):
    response = internal_client.get("/internal/branches/1/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json() == []


# ---- GET /internal/branches/list ----

def test_list_branches_returns_all(two_branches):
    response = internal_client.get("/internal/branches/list", headers=VALID_HEADERS)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    labels = {b["label"] for b in results}
    assert labels == {"Toulouse Esquirol", "Caussade"}


def test_list_branches_without_api_key_returns_error():
    response = internal_client.get("/internal/branches/list")
    assert response.status_code == 422


def test_list_branches_with_wrong_api_key_returns_error():
    response = internal_client.get("/internal/branches/list", headers={"x-api-key": "wrong-key"})
    assert response.status_code == 403
