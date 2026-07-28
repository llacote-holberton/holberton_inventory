"""Test module for web client"""
import os
import sys
from pathlib import Path

# Adding project's root in paths to explore as usual.
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Making the usual import to get local environment variables.
from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

# Setting up actual tests
import httpx
import pytest

# Retrieving port from environment as usual.
CLIENT_PORT = os.getenv("CLIENT_PORT", "8080")
BASE_URL = f"http://localhost:{CLIENT_PORT}"


def test_health_check():
    """Ensures that /api/health REST endpoint answers corerctly (200)."""
    response = httpx.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "client_web"}


def test_static_files_serve_index():
    """Checks that root '/' corectly serves HTML."""
    response = httpx.get(f"{BASE_URL}/")
    
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
