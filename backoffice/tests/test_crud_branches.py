#!/usr/bin/env python3
"""Unit tests for branch CRUD database operations."""

from db_models import Branch, User, UserRole
from crud import (
    list_branches,
    list_branches_ordered_by_label,
    get_branches_with_active_managers,
    find_branches_by_name,
)

# ========== BRANCH CRUD TESTS ==========

def test_list_branches(db):
    """Verifies that list_branches retrieves all branches in database."""
    b1 = Branch(label="Toulouse")
    b2 = Branch(label="Bordeaux")
    db.add_all([b1, b2])
    db.commit()

    branches = list_branches(db)

    assert len(branches) == 2
    assert {b.label for b in branches} == {"Toulouse", "Bordeaux"}


def test_list_branches_ordered_by_label(db):
    """Verifies that branches are returned in strict alphabetical order (A-Z)."""
    db.add_all([
        Branch(label="Toulouse"),
        Branch(label="Bordeaux"),
        Branch(label="Paris"),
    ])
    db.commit()

    branches = list_branches_ordered_by_label(db)

    labels = [b.label for b in branches]
    assert labels == ["Bordeaux", "Paris", "Toulouse"]


def test_find_branches_by_name(db):
    """Verifies case-insensitive partial substring search on branch labels."""
    db.add_all([
        Branch(label="Bordeaux"),
        Branch(label="Bourges"),
        Branch(label="Paris"),
    ])
    db.commit()

    # Search with lowercase substring "bo"
    results = find_branches_by_name(db, search_string="bo")
    assert len(results) == 2
    assert [b.label for b in results] == ["Bordeaux", "Bourges"]

    # Search with uppercase substring "PAR"
    results_par = find_branches_by_name(db, search_string="PAR")
    assert len(results_par) == 1
    assert results_par[0].label == "Paris"

    # Search non-matching substring
    results_empty = find_branches_by_name(db, search_string="xyz")
    assert len(results_empty) == 0


def test_get_branches_with_active_managers(db):
    """
    Verifies retrieving branches with eagerly loaded active managers.
    Must exclude:
    - Inactive managers
    - Non-manager users (e.g., Admins)
    """
    b_bordeaux = Branch(label="Bordeaux")
    b_lyon = Branch(label="Lyon")
    db.add_all([b_bordeaux, b_lyon])
    db.commit()

    # 1. Active manager on Bordeaux -> SHOULD BE INCLUDED
    u1 = User(name="Alice", password_hash="h1", role=UserRole.MANAGER, is_active=True, branch_id=b_bordeaux.id)
    # 2. Inactive manager on Bordeaux -> SHOULD BE EXCLUDED
    u2 = User(name="Bob", password_hash="h2", role=UserRole.MANAGER, is_active=False, branch_id=b_bordeaux.id)
    # 3. Active admin on Bordeaux -> SHOULD BE EXCLUDED (wrong role)
    u3 = User(name="Charlie", password_hash="h3", role=UserRole.ADMIN, is_active=True, branch_id=b_bordeaux.id)

    db.add_all([u1, u2, u3])
    db.commit()

    branches = get_branches_with_active_managers(db)

    assert len(branches) == 2
    assert branches[0].label == "Bordeaux"
    assert branches[1].label == "Lyon"

    bordeaux_managers = branches[0].managers
    assert len(bordeaux_managers) == 1
    assert bordeaux_managers[0].name == "Alice"

    assert len(branches[1].managers) == 0
