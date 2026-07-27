"""Test module dedicated to asserting endpoints of Internal API used by AI"""
# Note: thanks Claude for creating a nearly complete stub to adjust. :)

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

from db_models import Base, Branch, Stock
from database import get_db
from api_models import StockOut

from internal_api import app, INTERNAL_API_KEY, verify_internal_key


# INTERNAL_API_KEY override to not depend on presence of .env
#   with proper variable.
TEST_API_KEY = "cle-de-test-super-securisee"
VALID_HEADERS = {"x-api-key": TEST_API_KEY}

@pytest.fixture(autouse=True)
def override_api_key(monkeypatch):
    # On force l'API à utiliser cette même clé pendant les tests
    monkeypatch.setattr("internal_api.INTERNAL_API_KEY", TEST_API_KEY)


# ---- Setting up test DB, one connexion, one shared database for all tests ----
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
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

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    db = TestSessionLocal()
    yield db
    db.close()


@pytest.fixture
def two_branches(db_session):
    esquirol = Branch(id=1, label="Toulouse Esquirol")
    caussade = Branch(id=4, label="Caussade")
    db_session.add_all([esquirol, caussade])
    db_session.commit()
    return esquirol, caussade


@pytest.fixture
def stock_data(db_session, two_branches):
    """Produit 6 présent dans les deux branches, quantités différentes."""
    db_session.add_all([
        Stock(branch_id=1, product_id=6, quantity=15),
        Stock(branch_id=4, product_id=6, quantity=55),
        Stock(branch_id=4, product_id=2, quantity=777),
    ])
    db_session.commit()


# ---- GET /internal/branches/{branch_id}/stock/{product_id} ----

def test_get_stock_existing_line_returns_quantity(stock_data):
    response = client.get("/internal/branches/4/stock/6", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json() == {"branch_id": 4, "product_id": 6, "quantity": 55}


def test_get_stock_missing_line_returns_zero_not_404(two_branches):
    response = client.get("/internal/branches/1/stock/999", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json()["quantity"] == 0


def test_get_stock_without_api_key_returns_error(stock_data):
    response = client.get("/internal/branches/4/stock/6")
    # Must accept 422 as valid response, means "Unprocessable request"
    assert response.status_code in (401, 403, 422)


def test_get_stock_with_wrong_api_key_returns_error(stock_data):
    response = client.get(
        "/internal/branches/4/stock/6",
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code in (401, 403)


# ---- GET /internal/products/{product_id}/stocks ----
def test_stock_by_product_across_branches(stock_data):
    response = client.get("/internal/products/6/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    result = response.json()
    assert result["product_id"] == 6
    assert result["total_quantity"] == 70  # 15 + 55
    assert len(result["details"]) == 2
    branch_ids = {entry["branch_id"] for entry in result["details"]}
    assert branch_ids == {1, 4}


def test_stock_by_product_with_no_stock_returns_empty_summary(two_branches):
    response = client.get("/internal/products/999/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    result = response.json()
    assert result["product_id"] == 999
    assert result["total_quantity"] == 0
    assert result["details"] == []



# ---- GET /internal/branches/{branch_id}/stock ----
def test_stock_by_branch_lists_all_products(stock_data):
    response = client.get("/internal/branches/4/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    product_ids = {r["product_id"] for r in results}
    assert product_ids == {6, 2}


def test_stock_by_branch_with_no_stock_returns_empty_list(two_branches):
    response = client.get("/internal/branches/1/stocks", headers=VALID_HEADERS)
    assert response.status_code == 200
    assert response.json() == []

