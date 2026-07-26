import os
import httpx
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

# Par défaut : accès direct au conteneur de l'API Produit, tel que mappé
# par le docker-compose du Backoffice (port hôte 5000, confirmé via
# `docker ps` : 0.0.0.0:5000->5000/tcp). Si product_mcp_server tourne
# lui-même dans le même réseau Compose, passer
# PRODUCT_API_URL=http://external-products-api:5000 à la place (ou le
# nom de service réel du conteneur, ex. products-api).
PRODUCT_API_URL = os.getenv("PRODUCT_API_URL", "http://localhost:5000")
BACKOFFICE_API_URL = os.getenv("BACKOFFICE_API_URL", "http://localhost:8002")
# Clé attendue par le header X-API-KEY de l'API interne du Backoffice
# (voir backoffice/internal_api.py : verify_internal_key). Doit être la
# même valeur que INTERNAL_API_KEY dans le .env du Backoffice.
BACKOFFICE_API_KEY = os.getenv("BACKOFFICE_API_KEY", "")

mcp = FastMCP("product-mcp-server", host="127.0.0.1", port=8001)

# --------------------------------------------------------------------------
# Structures de sortie (on ne renvoie que ce dont l'agent a besoin, pas tout
# ce que l'API Produit peut exposer par ailleurs — cf. discussion sur
# Pydantic : un modèle par forme de donnée, pas un modèle par endpoint)
# --------------------------------------------------------------------------

class ProductSummary(BaseModel):
    """Résumé d'un produit, utilisé pour la liste/recherche de produits."""
    id: int
    sku: str
    name: str
    category: str
    unit_price: float


class ProductDetails(BaseModel):
    """Détails complets d'un produit, utilisés pour une consultation ciblée."""
    id: int
    sku: str
    name: str
    description: str | None = None
    category: str
    brand: str | None = None
    unit_price: float
    currency: str
    discontinued: bool = False
    tags: list[str] = []


# --------------------------------------------------------------------------
# Erreurs explicites
# --------------------------------------------------------------------------

class ProductNotFoundError(Exception):
    """Le produit demandé n'existe pas dans l'API Produit."""


class ProductAPIError(Exception):
    """L'API Produit est injoignable ou renvoie une erreur inattendue."""


async def _request_product_api(path: str, params: dict | None = None) -> httpx.Response:
    """
    Centralise les appels HTTP vers l'API Produit et traduit les échecs en
    erreurs claires :
      - erreur réseau / timeout            -> ProductAPIError
      - statut 404                         -> ProductNotFoundError
      - autre statut >= 400                -> ProductAPIError
    Le message d'erreur renvoyé par l'API elle-même (champ "message" du
    format {"error": ..., "message": ...}) est repris tel quel quand il
    est disponible, pour rester au plus près de ce que l'API a réellement
    signalé (ex. produit non trouvé vs erreur simulée avec force_error).
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{PRODUCT_API_URL}{path}", params=params)
    except httpx.RequestError as exc:
        raise ProductAPIError(
            f"Impossible de contacter l'API Produit ({PRODUCT_API_URL}) : {exc}"
        ) from exc

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("message", resp.text)
        except ValueError:
            detail = resp.text

        if resp.status_code == 404:
            raise ProductNotFoundError(detail)
        raise ProductAPIError(
            f"L'API Produit a répondu avec une erreur {resp.status_code} : {detail}"
        )

    return resp


# --------------------------------------------------------------------------
# Tools exposés à l'agent IA
# --------------------------------------------------------------------------

@mcp.tool()
async def list_products(
    q: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    Liste ou recherche des produits, avec un résumé (id, sku, nom,
    catégorie, prix). q filtre par texte (nom/SKU/description/tags),
    category filtre par catégorie exacte, min_price/max_price filtrent
    par fourchette de prix.
    """
    params = {"limit": limit}
    if q:
        params["q"] = q
    if category:
        params["category"] = category
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price

    resp = await _request_product_api("/api/v1/products", params=params)
    data = resp.json()
    raw_products = data.get("items", data) if isinstance(data, dict) else data
    summaries = [
        ProductSummary(
            id=p["id"], sku=p["sku"], name=p["name"],
            category=p["category"], unit_price=p["unit_price"],
        )
        for p in raw_products
    ]
    return [s.model_dump() for s in summaries]


@mcp.tool()
async def get_product_details(id_or_sku: str) -> dict:
    """
    Retourne les détails complets (nom, description, prix, catégorie,
    marque, tags) d'un produit identifié par son id numérique ou son SKU.
    Lève une erreur explicite si le produit n'existe pas, ou si l'API
    Produit est injoignable.
    """
    resp = await _request_product_api(f"/api/v1/products/{id_or_sku}")
    data = resp.json()
    details = ProductDetails(
        id=data["id"], sku=data["sku"], name=data["name"],
        description=data.get("description"), category=data["category"],
        brand=data.get("brand"), unit_price=data["unit_price"],
        currency=data["currency"], discontinued=data.get("discontinued", False),
        tags=data.get("tags", []),
    )
    return details.model_dump()


@mcp.tool()
async def get_stock(product_id: int, branch_id: int) -> dict:
    """
    Retourne la quantité en stock d'un produit précis dans une branche
    précise. Les deux identifiants sont obligatoires (c'est une exigence
    de l'API interne du Backoffice, qui n'expose pas de listing global).
    Si l'agent ne connaît que l'un des deux, il doit d'abord le
    déterminer autrement (ex. lister les branches ou les produits)
    avant d'appeler ce tool. Ces données viennent UNIQUEMENT du
    Backoffice : l'API Produit externe ne connaît pas les quantités en
    stock.
    """
    params = {"product_id": product_id, "branch_id": branch_id}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BACKOFFICE_API_URL}/internal/stock",
                params=params,
                headers={"X-API-KEY": BACKOFFICE_API_KEY},
            )
    except httpx.RequestError as exc:
        raise ProductAPIError(
            f"Impossible de contacter le Backoffice ({BACKOFFICE_API_URL}) : {exc}"
        ) from exc

    if resp.status_code == 403:
        raise ProductAPIError(
            "Authentification refusée par le Backoffice (BACKOFFICE_API_KEY "
            "incorrecte ou absente)."
        )
    if resp.status_code >= 400:
        raise ProductAPIError(
            f"Le Backoffice a répondu avec une erreur {resp.status_code}."
        )
    return resp.json()


if __name__ == "__main__":
    # transport HTTP car ce service tourne dans son propre conteneur Docker,
    # séparé du service ai_service qui va s'y connecter par le réseau.
    mcp.run(transport="streamable-http")
