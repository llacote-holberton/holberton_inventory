#!/usr/bin/env python3
"""Unit tests for stock CRUD database operations."""

import pytest
from db_models import Branch
from crud import (
    get_stock,
    set_stock,
    remove_stock,
    list_stocks_for_product,
    list_stocks_for_branch,
    delete_stock,
    InsufficientStockError,
)


# ========== FIXTURES ==========

@pytest.fixture
def sample_branches(db):
    """Creates two branches required to satisfy foreign key constraints."""
    b1 = Branch(label="Bordeaux Test")
    b2 = Branch(label="Lyon Test")
    db.add_all([b1, b2])
    db.commit()
    db.refresh(b1)
    db.refresh(b2)
    return b1, b2


# ========== STOCK CRUD TESTS ==========

def test_get_stock_returns_none_when_empty(db, sample_branches):
    """Verifies get_stock returns None when no row exists for product/branch."""
    branch, _ = sample_branches
    stock = get_stock(db, product_id=101, branch_id=branch.id)
    assert stock is None


def test_set_stock_insert_and_update(db, sample_branches):
    """Verifies set_stock creates a row if missing and updates it if present."""
    branch, _ = sample_branches

    qty1 = set_stock(db, product_id=101, branch_id=branch.id, quantity=50)
    assert qty1 == 50

    stock = get_stock(db, product_id=101, branch_id=branch.id)
    assert stock is not None
    assert stock.quantity == 50

    qty2 = set_stock(db, product_id=101, branch_id=branch.id, quantity=120)
    assert qty2 == 120

    stock_updated = get_stock(db, product_id=101, branch_id=branch.id)
    assert stock_updated.quantity == 120


def test_remove_stock_success(db, sample_branches):
    """Verifies successful stock reduction."""
    branch, _ = sample_branches
    set_stock(db, product_id=101, branch_id=branch.id, quantity=100)

    remaining = remove_stock(db, branch_id=branch.id, product_id=101, amount=30)

    assert remaining == 70
    stock = get_stock(db, product_id=101, branch_id=branch.id)
    assert stock.quantity == 70


def test_remove_stock_insufficient_stock_raises_error(db, sample_branches):
    """Verifies that removing more than available stock raises InsufficientStockError and leaves stock unchanged."""
    branch, _ = sample_branches
    set_stock(db, product_id=101, branch_id=branch.id, quantity=20)

    with pytest.raises(InsufficientStockError) as exc_info:
        remove_stock(db, branch_id=branch.id, product_id=101, amount=50)

    assert exc_info.value.available == 20

    stock = get_stock(db, product_id=101, branch_id=branch.id)
    assert stock.quantity == 20


def test_remove_stock_non_existing_returns_none(db, sample_branches):
    """Verifies that attempting to remove stock from a non-existent row returns None."""
    branch, _ = sample_branches
    result = remove_stock(db, branch_id=branch.id, product_id=999, amount=10)
    assert result is None


def test_list_stocks_for_product(db, sample_branches):
    """Verifies listing stock levels for a specific product across multiple branches."""
    branch1, branch2 = sample_branches

    set_stock(db, product_id=101, branch_id=branch1.id, quantity=15)
    set_stock(db, product_id=101, branch_id=branch2.id, quantity=40)
    set_stock(db, product_id=202, branch_id=branch1.id, quantity=5)

    stocks_101 = list_stocks_for_product(db, product_id=101)

    assert len(stocks_101) == 2
    assert {s.branch_id for s in stocks_101} == {branch1.id, branch2.id}


def test_list_stocks_for_branch(db, sample_branches):
    """Verifies listing all product stocks contained in a single branch."""
    branch1, branch2 = sample_branches

    set_stock(db, product_id=101, branch_id=branch1.id, quantity=10)
    set_stock(db, product_id=202, branch_id=branch1.id, quantity=25)
    set_stock(db, product_id=303, branch_id=branch2.id, quantity=99)

    branch1_stocks = list_stocks_for_branch(db, branch_id=branch1.id)

    assert len(branch1_stocks) == 2
    assert {s.product_id for s in branch1_stocks} == {101, 202}


def test_delete_stock(db, sample_branches):
    """Verifies complete deletion of a stock record."""
    branch, _ = sample_branches
    set_stock(db, product_id=101, branch_id=branch.id, quantity=50)

    delete_stock(db, product_id=101, branch_id=branch.id)

    stock = get_stock(db, product_id=101, branch_id=branch.id)
    assert stock is None
