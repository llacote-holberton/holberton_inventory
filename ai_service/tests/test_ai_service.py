import os
import sys
from pathlib import Path

# Adding project's root in paths to explore as usual.
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# Making the usual import to get local environment variables.
from dotenv import load_dotenv
load_dotenv(root_dir / ".env")

import httpx
import pytest

# Get AI listen port from env var or fallback value.
raw_port = os.getenv("AI_SERVICE_PORT")
port = raw_port if raw_port else "8003"
# Should work whether in or out docker.
BASE_URL = f"http://127.0.0.1:{port}"


# Most basic healthcheck test.
def test_ai_service_health():
    """Vérifie que l'API FastAPI réagit correctement sur la route /health."""
    url = f"{BASE_URL}/health"
    response = httpx.get(url, timeout=5.0)

    # 1. Vérification du statut 200
    assert response.status_code == 200, f"Erreur HTTP: {response.status_code} - {response.text}"

    # 2. Vérification de la réponse JSON du healthcheck
    assert response.json() == {"status": "ok"}, f"Réponse inattendue: {response.json()}"
