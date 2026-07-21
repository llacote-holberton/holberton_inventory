from fastmcp import FastMCP

# Initialisation du serveur
mcp = FastMCP("ProductInventoryServer")

# Simulation de l'API externe Produit
PRODUCTS = {
    "P100": {"name": "Clavier", "price": 90.00, "category": "Tech"},
    "P200": {"name": "Souris", "price": 45.00, "category": "Tech"},
}

@mcp.tool()
def list_products() -> list[dict]:
    """liste des identifiants et noms des produits disponibles."""
    return [{"id": k, "name": v["name"]} for k, v in PRODUCTS.items()]

@mcp.tool()
def get_product_details(product_id: str) -> dict:
    """détails complets d'un produit à partir de son ID."""
    return PRODUCTS.get(product_id, {"error": "Produit introuvable"})

if __name__ == "__main__":
    mcp.run()