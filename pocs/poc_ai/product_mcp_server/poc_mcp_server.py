# product_mcp_server_http.py
from fastmcp import FastMCP

# Initialisation du serveur
mcp = FastMCP("ProductCatalogServer")

# Simulation de la base/API Produit
MOCK_PRODUCTS = {
    "P100": {"name": "Clavier Mécanique", "price": 89.99, "category": "Tech"},
    "P200": {"name": "Souris Sans Fil", "price": 45.00, "category": "Tech"},
}

@mcp.tool()
def list_products() -> list[dict]:
    """Retourne la liste complète des identifiants et noms des produits disponibles."""
    return [{"id": k, "name": v["name"]} for k, v in MOCK_PRODUCTS.items()]

@mcp.tool()
def get_product_details(product_id: str) -> dict:
    """Retourne les détails complets d'un produit (nom, prix, catégorie) à partir de son ID."""
    return MOCK_PRODUCTS.get(product_id, {"error": "Produit introuvable"})

if __name__ == "__main__":
    # Lancement du serveur en mode HTTP / SSE sur le port 8000
    mcp.run(transport="sse", host="0.0.0.0", port=8000)