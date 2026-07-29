/**
 * Interface manager (stock de la branche).
 *
 * TODO (une fois l'API du Backoffice prête côté binôme) :
 *   - Remplacer STOCK_API_URL par le vrai endpoint (ex. GET /api/stock/mine)
 *   - Envoyer le token d'authentification (ex. header Authorization) —
 *     rappel de la consigne : l'accès au Backoffice doit être authentifié
 *   - Remplacer adjustStock() par de vrais appels
 *     POST /api/stock/add et POST /api/stock/remove
 *   - Retirer MOCK_STOCK : ces données ne servent qu'à visualiser
 *     l'interface avant que le Backoffice soit prêt.
 */

function checkAuth() {
    // Si on est déjà sur la page de login, rien à faire
    if (window.location.pathname.includes("/login")) return;

    const token = localStorage.getItem("token");
    if (!token) {
        // Put /ui/login once it's good'
        window.location.href = "localhost:8000/ui/login";
    }
}

// Execute immediately
// (FIXME maybe should be separate script loaded in header
checkAuth();

// ============== 3. Provides a fetch wrapper to automatically use authn token ===================
async function apiFetch(url, options = {}) {
    const token = localStorage.getItem("token");
    
    // Fusionner les headers existants avec le token
    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };

    const response = await fetch(url, options);

    // Si le token est expiré ou invalide (401), renvoyer vers le login
    if (response.status === 401) {
        localStorage.clear();
        // Put /ui/login once it's good'
        window.location.href = "localhost:8000/ui/login";
        return;
    }

    return response;
}



const STOCK_API_URL = "http://localhost:8000/api/stock/mine";

const MOCK_STOCK = [
  { id: 32, name: "Legacy VGA Adapter", category: "Accessories", supplier: "OpsReady Warehouse", quantity: 15 },
  { id: 33, name: "RFID Access Card Pack", category: "Security", supplier: "WebCraft Devices", quantity: 0 },
  { id: 34, name: "USB Security Key", category: "Security", supplier: "WebCraft Devices", quantity: 42 },
];

// Utilisé uniquement en mode mock pour simuler l'enrichissement que le
// vrai Backoffice ferait via l'API Produit (nom, catégorie, fournisseur)
// quand on ajoute un produit pas encore stocké dans la branche.
const MOCK_CATALOG = {
  32: { name: "Legacy VGA Adapter", category: "Accessories", supplier: "OpsReady Warehouse" },
  33: { name: "RFID Access Card Pack", category: "Security", supplier: "WebCraft Devices" },
  34: { name: "USB Security Key", category: "Security", supplier: "WebCraft Devices" },
  40: { name: "Wireless Presenter Clicker", category: "Accessories", supplier: "ClickTech" },
};

const stockListEl = document.getElementById("stock-list");
let stockData = [];

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderStock() {
  stockListEl.innerHTML = "";

  stockData.forEach((item) => {
    const card = document.createElement("div");
    card.className = "stock-card";
    card.innerHTML = `
      <div class="stock-tag">#${item.id}</div>
      <div class="stock-name">${item.name}</div>
      <div class="stock-meta">
        <span>Catégorie : ${item.category}</span>
        <span>Fournisseur : ${item.supplier}</span>
      </div>
      <div class="stock-qty">
        <span class="current ${item.quantity === 0 ? "zero" : ""}">Quantité actuelle : ${item.quantity}</span>
        <input type="number" min="1" value="1" aria-label="Quantité à ajouter ou retirer pour ${item.name}">
        <button class="add" type="button">Ajouter</button>
        <button class="remove" type="button">Retirer</button>
      </div>
    `;

    const input = card.querySelector("input");
    card.querySelector(".add").addEventListener("click", () => {
      adjustStock(item.id, parseInt(input.value, 10) || 0);
    });
    card.querySelector(".remove").addEventListener("click", () => {
      adjustStock(item.id, -(parseInt(input.value, 10) || 0));
    });

    stockListEl.appendChild(card);
  });
}

async function adjustStock(productId, delta) {
  const item = stockData.find((p) => p.id === productId);
  if (!item) return;

  const newQuantity = item.quantity + delta;
  if (newQuantity < 0) {
    alert("La quantité en stock ne peut pas devenir négative.");
    return;
  }

  // TODO : remplacer par un vrai appel POST /api/stock/add ou
  // /api/stock/remove vers le Backoffice une fois l'endpoint prêt.
  // Pour l'instant, mise à jour locale uniquement (mode mock).
  item.quantity = newQuantity;
  renderStock();
}

async function loadStock() {
  try {
    const response = await fetch(STOCK_API_URL);
    if (!response.ok) throw new Error(`Statut HTTP ${response.status}`);
    stockData = await response.json();
  } catch (error) {
    // Le Backoffice n'est pas encore prêt : on retombe sur des données de
    // démonstration pour pouvoir travailler l'interface dès maintenant.
    stockData = MOCK_STOCK;
  }
  renderStock();
}

function addNewProductStock(productId, quantity) {
  const existing = stockData.find((p) => p.id === productId);
  if (existing) {
    // Le produit est déjà en stock dans cette branche : on incrémente au
    // lieu de créer une deuxième ligne pour le même produit.
    adjustStock(productId, quantity);
    return;
  }

  // TODO : en vrai, le Backoffice doit d'abord vérifier que ce produit
  // existe réellement (via l'API Produit, à travers le serveur MCP ou un
  // appel direct côté Backoffice) avant de créer une ligne de stock, et
  // renvoyer nom/catégorie/fournisseur depuis cette vérification plutôt
  // que depuis un catalogue local comme ici.
  const catalogEntry = MOCK_CATALOG[productId] || {
    name: `Produit #${productId} (non reconnu en mode mock)`,
    category: "Inconnue",
    supplier: "Inconnu",
  };

  stockData.push({ id: productId, quantity, ...catalogEntry });
  renderStock();
}

document.getElementById("new-stock-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const idInput = document.getElementById("new-product-id");
  const qtyInput = document.getElementById("new-product-qty");
  const productId = parseInt(idInput.value, 10);
  const quantity = parseInt(qtyInput.value, 10);
  if (!productId || !quantity || quantity <= 0) return;

  addNewProductStock(productId, quantity);
  idInput.value = "";
  qtyInput.value = "1";
});

loadStock();
