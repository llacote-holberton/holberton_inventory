/**
 * Interface manager (stock de la branche).
 */

let userBranchId = null;
let stockData = [];
const stockListEl = document.getElementById("stock-list");

// URL de l'API Produit (Port 5000) et cache local
const PRODUCTS_API_URL = "http://localhost:5000";
const productCache = new Map();

// Helper de sécurité XSS
function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

// 1. Initialisation de la page
async function init() {
  checkAuth();

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "/ui/login";
    });
  }

  const whoamiResp = await apiFetch("/whoami");
  if (!whoamiResp || !whoamiResp.ok) return;

  const userData = await whoamiResp.json();
  userBranchId = userData.branch_id;

  if (!userBranchId) {
    alert("Erreur : Aucun identifiant de branche associé à ce compte manager.");
    return;
  }

  await loadStock();
}

// 2. Fetch wrapper authentifié (pour l'API Backoffice sur le port 8000)
async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("token");

  options.headers = {
    ...options.headers,
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };

  const response = await fetch(url, options);

  if (response.status === 401) {
    localStorage.clear();
    window.location.href = "/ui/login";
    return null;
  }

  return response;
}

// 3. Récupération des détails d'un produit depuis l'API Produit (Port 5000)
async function getProductInfo(productId) {
  if (productCache.has(productId)) {
    return productCache.get(productId);
  }

  try {
    const response = await fetch(`${PRODUCTS_API_URL}/api/v1/products/${productId}`);
    if (response.ok) {
      const data = await response.json();
      productCache.set(productId, data);
      return data;
    }
  } catch (err) {
    console.warn(`Impossible de contacter l'API Produit pour le produit #${productId}:`, err);
  }

  return null;
}

// 4. Chargement des stocks depuis l'API Backoffice + enrichissement via l'API Produit
async function loadStock() {
  if (!userBranchId) return;

  try {
    const response = await apiFetch(`/branches/${userBranchId}/stocks`);
    if (!response || !response.ok) {
      throw new Error(`Statut HTTP ${response?.status}`);
    }

    stockData = await response.json();

    // Enrichissement en parallèle pour chaque produit
    await Promise.all(
      stockData.map(async (item) => {
        const info = await getProductInfo(item.product_id);
        if (info) {
          item.name = info.name || info.label || info.title;
          item.category = info.category;
          // ✅ On mappe correctement supplier_name depuis la réponse API
          item.supplier_name = info.supplier_name || info.supplier || info.brand;
        }
      })
    );

    renderStock();
  } catch (error) {
    console.error("Erreur de chargement des stocks:", error);
    if (stockListEl) {
      stockListEl.innerHTML = `<p class="placeholder">Erreur lors du chargement des stocks.</p>`;
    }
  }
}

// 5. Affichage du stock
function renderStock() {
  if (!stockListEl) return;
  stockListEl.innerHTML = "";

  if (stockData.length === 0) {
    stockListEl.innerHTML = `<p class="placeholder">Aucun produit en stock pour cette branche.</p>`;
    return;
  }

  stockData.forEach((item) => {
    const card = document.createElement("div");
    card.className = "stock-card";

    const name = item.name || `Produit #${item.product_id}`;
    const category = item.category || "Inconnue";
    // ✅ Compatible supplier_name, supplier ou "Inconnu"
    const supplier = item.supplier_name || item.supplier || "Inconnu";

    card.innerHTML = `
      <div class="stock-tag">#${item.product_id}</div>
      <div class="stock-name">${escapeHtml(name)}</div>
      <div class="stock-meta">
        <span>Catégorie : ${escapeHtml(category)}</span>
        <span>Fournisseur : ${escapeHtml(supplier)}</span>
      </div>
      <div class="stock-qty">
        <span class="current ${item.quantity === 0 ? "zero" : ""}">Quantité actuelle : ${item.quantity}</span>
        <input type="number" min="1" value="1" aria-label="Quantité à ajuster pour ${escapeHtml(name)}">
        <button class="add" type="button">Ajouter</button>
        <button class="remove" type="button">Retirer</button>
      </div>
    `;

    const input = card.querySelector("input");

    card.querySelector(".add").addEventListener("click", () => {
      const amount = parseInt(input.value, 10) || 0;
      if (amount > 0) addStock(item.product_id, amount);
    });

    card.querySelector(".remove").addEventListener("click", () => {
      const amount = parseInt(input.value, 10) || 0;
      if (amount > 0) removeStock(item.product_id, amount);
    });

    stockListEl.appendChild(card);
  });
}

// 6. Action d'ajout de stock
async function addStock(productId, amount) {
  if (!userBranchId) return;

  const response = await apiFetch(`/branches/${userBranchId}/stock/add`, {
    method: "POST",
    body: JSON.stringify({ product_id: productId, amount: amount }),
  });

  if (!response) return;

  if (response.ok) {
    await loadStock();
  } else {
    const err = await response.json();
    alert(`Erreur : ${err.detail || "Impossible d'ajouter le stock."}`);
  }
}

// 7. Action de retrait de stock
async function removeStock(productId, amount) {
  if (!userBranchId) return;

  const response = await apiFetch(`/branches/${userBranchId}/stock/remove`, {
    method: "POST",
    body: JSON.stringify({ product_id: productId, amount: amount }),
  });

  if (!response) return;

  if (response.ok) {
    await loadStock();
  } else {
    const err = await response.json();
    alert(`Erreur : ${err.detail || "Impossible de retirer le stock."}`);
  }
}

// 8. Formulaire d'ajout d'une nouvelle référence par ID
document.getElementById("new-stock-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const idInput = document.getElementById("new-product-id");
  const qtyInput = document.getElementById("new-product-qty");

  const productId = parseInt(idInput.value, 10);
  const quantity = parseInt(qtyInput.value, 10);

  if (!productId || !quantity || productId <= 0 || quantity <= 0) {
    alert("Veuillez saisir un ID produit valide et une quantité strictement positive.");
    return;
  }

  await addStock(productId, quantity);

  idInput.value = "";
  qtyInput.value = "1";
});

document.addEventListener("DOMContentLoaded", init);
