# ========== IMPORTS AND "INITIAL SETUP" ==========
# REQUIRED to reconstruct dynamically the path to parent folder in which
#   the models are located.
import os
import sys
from pathlib import Path

# Adds the parent of current folder to the list of paths
#   to parse when looking for modules (a bit like bash PATH)
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from dotenv import load_dotenv
import httpx
import pytest
import json

# REQUIRED to exploit "local environment variables"
load_dotenv(root_dir / ".env")

# 1. Forcing explicit 127.0.0.1 (IPv4) to avoid httxp trying ipv6 protocol.
# 2. Retrieving the port from env.
port = os.getenv("MCP_SERVER_PORT", "8001")
BASE_URL = f"http://127.0.0.1:{port}/mcp"


def test_mcp_server_health_and_init():
    """Checks the server properly answers a 'JSON-RPC initialize' request."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest-client", "version": "1.0.0"},
        },
    }

    # Mantadory headers considering serveur uses Streamable HTTP protocol
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    response = httpx.post(BASE_URL, json=payload, headers=headers, timeout=5.0)

    # 1. Checks we get HTTP 200 code
    assert response.status_code == 200, f"Erreur HTTP: {response.status_code} - {response.text}"

    # 2. Tries to extract the json data from the SSE stream.
    # Intermediate step required because just doing `data = response.json()` couldn't work
    #   with Streamable HTTP protocol as answer is not raw json but a SSE stream.
    json_data = None
    for line in response.text.splitlines():
        if line.startswith("data: "):
            json_str = line[6:].strip()  # On retire le préfixe "data: "
            json_data = json.loads(json_str)
            break

    assert json_data is not None, f"Aucune donnée JSON-RPC trouvée dans la réponse SSE : {response.text}"

    # 3. Checks the JSON structure in Response's body is as expected
    assert "result" in json_data, f"Réponse invalide : {json_data}"
    assert json_data["result"]["serverInfo"]["name"] == "product-mcp-server"
