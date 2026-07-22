

import os
import httpx
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

PRODUCT_API_URL = os.getenv("PRODUCT_API_URL", "http://product_api:8080")
BACKOFFICE_API_URL = os.getenv("BACKOFFICE_API_URL", "http://backoffice:8000")

mcp = FastMCP("product-mcp-server")


# --------------------------------------------------------------------------
# Structures de sortie (on ne renvoie que ce dont l'agent a besoin, pas tout
# ce que l'API Produit peut exposer par ailleurs)
# --------------------------------------------------------------------------

class ProductSummary(BaseModel):
    """Résumé d'un produit, utilisé pour la liste des produits."""
    id: str
    name: str
    price: float | None = None


class ProductDetails(BaseModel):
    """Détails complets d'un produit, utilisés pour une consultation ciblée."""
    id: str
    name: str
    description: str | None = None
    price: float | None = None


# --------------------------------------------------------------------------
# Erreurs explicites
# --------------------------------------------------------------------------

class ProductNotFoundError(Exception):
    """Le produit demandé n'existe pas dans l'API Produit."""


class ProductAPIError(Exception):
    """L'API Produit est injoignable ou renvoie une erreur inattendue."""


async def _request_product_api(path: str) -> httpx.Response:
    """
    Centralise les appels HTTP vers l'API Produit et traduit les échecs
    en erreurs claires et distinctes :
      - erreur réseau / timeout  -> ProductAPIError
      - statut 404               -> ProductNotFoundError
      - autre statut >= 400      -> ProductAPIError
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{PRODUCT_API_URL}{path}")
    except httpx.RequestError as exc:
        raise ProductAPIError(
            f"Impossible de contacter l'API Produit ({PRODUCT_API_URL}) : {exc}"
        ) from exc

    if resp.status_code == 404:
        raise ProductNotFoundError(
            f"Aucun produit trouvé pour la requête '{path}'."
        )
    if resp.status_code >= 400:
        raise ProductAPIError(
            f"L'API Produit a répondu avec une erreur "
            f"{resp.status_code} pour '{path}'."
        )
    return resp


# --------------------------------------------------------------------------
# Tools exposés à l'agent IA
# --------------------------------------------------------------------------

@mcp.tool()
async def list_products() -> list[dict]:
    """
    Liste tous les produits disponibles, avec un résumé (id, nom, prix).
    Lève une erreur explicite si l'API Produit est injoignable.
    """
    resp = await _request_product_api("/products")
    raw_products = resp.json()
    summaries = [
        ProductSummary(id=p["id"], name=p["name"], price=p.get("price"))
        for p in raw_products
    ]
    return [s.model_dump() for s in summaries]


@mcp.tool()
async def get_product_details(product_id: str) -> dict:
    """
    Retourne les détails complets (nom, description, prix) d'un produit.
    Lève une erreur explicite si le produit n'existe pas, ou si l'API
    Produit est injoignable.
    """
    resp = await _request_product_api(f"/products/{product_id}")
    data = resp.json()
    details = ProductDetails(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        price=data.get("price"),
    )
    return details.model_dump()


@mcp.tool()
async def get_stock(product_id: str | None = None, branch_id: int | None = None) -> list[dict]:
    """
    Retourne les quantités en stock, filtrables par produit et/ou par branche.
    Passer product_id pour "quel(s) magasin(s) ont ce produit ?".
    Passer branch_id pour "que contient telle branche ?".
    Ne rien passer pour tout récupérer.
    """
    params = {}
    if product_id:
        params["product_id"] = product_id
    if branch_id:
        params["branch_id"] = branch_id

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BACKOFFICE_API_URL}/api/stock", params=params)
    except httpx.RequestError as exc:
        raise ProductAPIError(
            f"Impossible de contacter le Backoffice ({BACKOFFICE_API_URL}) : {exc}"
        ) from exc

    if resp.status_code >= 400:
        raise ProductAPIError(
            f"Le Backoffice a répondu avec une erreur {resp.status_code}."
        )
    return resp.json()


if __name__ == "__main__":
    # transport HTTP car ce service tourne dans son propre conteneur Docker,
    # séparé du service ai_service qui va s'y connecter par le réseau.
    mcp.run(transport="streamable-http")
