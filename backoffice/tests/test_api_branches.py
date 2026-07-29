#!/usr/bin/env python3
"""End-to-end API tests for backoffice branches endpoints."""

# ========== AUTHENTICATION AND AUTHORIZATION TESTS ==========

def test_list_branches_without_token_returns_401(client):
    response = client.get("/branches")
    assert response.status_code == 401


def test_list_branches_with_invalid_token_returns_401(client):
    response = client.get("/branches", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert response.status_code == 401


def test_list_branches_with_manager_token_succeeds(client, manager_token, seed_branches_data):
    response = client.get(
        "/branches",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_list_branches_with_admin_token_succeeds(client, admin_token, seed_branches_data):
    response = client.get(
        "/branches",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


# ========== QUERY PARAMETERS AND ORDERING TESTS ==========

def test_list_branches_ordered_by_label_default(client, manager_token, seed_branches_data):
    response = client.get(
        "/branches",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    labels = [b["label"] for b in response.json()]
    assert labels == ["Bordeaux", "Bourges", "Paris"]


def test_list_branches_unordered_or_default_id(client, manager_token, seed_branches_data):
    response = client.get(
        "/branches?ordered_by_label=false",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    labels = [b["label"] for b in response.json()]
    assert labels == ["Paris", "Bordeaux", "Bourges"]


def test_list_branches_invalid_boolean_param_returns_422(client, manager_token):
    response = client.get(
        "/branches?ordered_by_label=invalid_bool_value",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 422


# ========== WITH_MANAGERS PARAMETER AND PERMISSIONS TESTS ==========

def test_list_branches_with_managers_as_admin_succeeds(client, admin_token, seed_branches_data):
    response = client.get(
        "/branches?with_managers=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    paris_branch = next(b for b in data if b["label"] == "Paris")
    assert "managers" in paris_branch
    assert paris_branch["managers"] is not None
    assert len(paris_branch["managers"]) == 1
    assert paris_branch["managers"][0]["name"] == "active_manager_paris"


def test_list_branches_with_managers_as_manager_returns_403(client, manager_token, seed_branches_data):
    response = client.get(
        "/branches?with_managers=true",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_list_branches_with_managers_false_as_manager_succeeds(client, manager_token, seed_branches_data):
    response = client.get(
        "/branches?with_managers=false",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


# ========== SEARCH BRANCHES ENDPOINT TESTS ==========

def test_search_branches_without_token_returns_401(client):
    response = client.get("/search/branches/Paris")
    assert response.status_code == 401


def test_search_branches_by_name_as_manager_succeeds(client, manager_token, seed_branches_data):
    response = client.get(
        "/search/branches/Paris",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["label"] == "Paris"


def test_search_branches_by_name_as_admin_succeeds(client, admin_token, seed_branches_data):
    response = client.get(
        "/search/branches/Bordeaux",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["label"] == "Bordeaux"


def test_search_branches_partial_match_succeeds(client, manager_token, seed_branches_data):
    response = client.get(
        "/search/branches/Bo",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    labels = [b["label"] for b in data]
    assert "Bordeaux" in labels
    assert "Bourges" in labels


def test_search_branches_no_match_returns_404(client, manager_token, seed_branches_data):
    response = client.get(
        "/search/branches/Toulouse",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "no_matching_branch_found"
