from fastmcp import FastMCP
from app.product_client import fetch_all_products, fetch_product_details
from app.stock_db import get_stock_by_product, get_stocks_by_branch

# Création de l'instance FastMCP
mcp = FastMCP(
    name="Retail Inventory MCP Server",
    instructions="Fournit des outils pour consulter le catalogue produits et les stocks en magasin."
)

@mcp.tool()
async def list_products() -> list[dict]:
    """
    Récupère la liste complète des produits disponibles dans le catalogue.
    Retourne l'ID, le nom et le prix de chaque produit.
    """
    return await fetch_all_products()

@mcp.tool()
async def get_product_info(product_id: str) -> dict:
    """
    Obtient les informations détaillées d'un produit spécifique à partir de son ID.
    """
    details = await fetch_product_details(product_id)
    if not details:
        return {"error": f"Produit avec l'ID '{product_id}' introuvable."}
    return details

@mcp.tool()
def check_product_stock_across_branches(product_id: str) -> list[dict]:
    """
    Vérifie la quantité disponible pour un produit donné (product_id) dans TOUTES les branches.
    """
    stocks = get_stock_by_product(product_id)
    if not stocks:
        return [{"message": f"Aucun stock trouvé pour le produit {product_id}."}]
    return stocks

@mcp.tool()
def list_branch_inventory(branch_name: str) -> list[dict]:
    """
    Liste tous les identifiants de produits et leurs quantités disponibles dans une branche donnée.
    """
    stocks = get_stocks_by_branch(branch_name)
    if not stocks:
        return [{"message": f"Aucun stock trouvé pour la branche '{branch_name}'."}]
    return stocks

if __name__ == "__main__":
    # Lance le serveur FastMCP en mode SSE sur le port 8000
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
