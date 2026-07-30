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

  // Récupération des infos de l'utilisateur connecté
  const whoamiResp = await apiFetch("/whoami");
  if (!whoamiResp || !whoamiResp.ok) return;

  const userData = await whoamiResp.json();
  userBranchId = userData.branch_id;

  if (!userBranchId) {
    customAlert("Erreur : Aucun identifiant de branche associé à ce compte manager.");
    return;
  }

  // Point 4: Récupération et affichage du nom de l'utilisateur et de sa branche
  await displayUserInfo(userData);

  await loadStock();
}

// Helper pour afficher les infos utilisateur et le nom de sa branche
async function displayUserInfo(userData) {
  const userNameEl = document.getElementById("user-display-name");
  const branchNameEl = document.getElementById("branch-display-name");

  if (userNameEl) {
    userNameEl.textContent = userData.username || userData.name || userData.sub || `Manager #${userData.user_id}`;
  }

  try {
    const res = await apiFetch("/branches");
    if (res && res.ok) {
      const branches = await res.json();
      const myBranch = branches.find((b) => b.id === userBranchId);
      if (branchNameEl) {
        branchNameEl.textContent = myBranch ? (myBranch.name || myBranch.label) : `Branche #${userBranchId}`;
      }
    }
  } catch (err) {
    console.warn("Impossible de récupérer le nom de la branche:", err);
    if (branchNameEl) branchNameEl.textContent = `Branche #${userBranchId}`;
  }
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

// 2bis alert helper
function customAlert(message, title = "Information") {
  let overlay = document.getElementById("custom-modal-overlay");

  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "custom-modal-overlay";
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box">
        <h3 class="modal-title" id="custom-modal-title"></h3>
        <div class="modal-body" id="custom-modal-message"></div>
        <div class="modal-actions">
          <button class="modal-btn" id="custom-modal-close" type="button">Compris</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const closeBtn = overlay.querySelector("#custom-modal-close");
    closeBtn.addEventListener("click", () => overlay.classList.remove("active"));
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("active");
    });
  }

  document.getElementById("custom-modal-title").textContent = title;
  document.getElementById("custom-modal-message").textContent = message;
  overlay.classList.add("active");
}




// 3. Récupération des détails d'un produit par ID (Port 5000)
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

//Adding function to find product from SKU or ID with Products API
async function resolveProductBySkuOrId(query) {
  const cleanQuery = String(query).trim();

  // Si c'est un identifiant numérique pur, on teste en direct l'endpoint par ID
  if (/^\d+$/.test(cleanQuery)) {
    const productById = await getProductInfo(parseInt(cleanQuery, 10));
    if (productById) return productById;
  }

  // Sinon (ou en fallback), recherche par SKU / mot-clé via l'endpoint de recherche
  try {
    const response = await fetch(`${PRODUCTS_API_URL}/api/v1/products/search?q=${encodeURIComponent(cleanQuery)}`);
    if (response.ok) {
      const searchData = await response.json();
      const results = searchData.results || [];

      // Recherche d'une correspondance exacte sur le SKU
      const exactSkuMatch = results.find(
        (p) => p.sku && p.sku.toLowerCase() === cleanQuery.toLowerCase()
      );

      if (exactSkuMatch) {
        productCache.set(exactSkuMatch.id, exactSkuMatch);
        return exactSkuMatch;
      }

      // Si pas de correspondance exacte mais des résultats, renvoyer le premier
      if (results.length > 0) {
        productCache.set(results[0].id, results[0]);
        return results[0];
      }
    }
  } catch (err) {
    console.warn(`Erreur lors de la recherche du produit "${cleanQuery}":`, err);
  }

  return null;
}

// 4. Chargement des stocks depuis l'API Backoffice + enrichissement
async function loadStock() {
  if (!userBranchId) return;

  try {
    const response = await apiFetch(`/branches/${userBranchId}/stocks`);
    if (!response || !response.ok) {
      throw new Error(`Statut HTTP ${response?.status}`);
    }

    stockData = await response.json();

    await Promise.all(
      stockData.map(async (item) => {
        const info = await getProductInfo(item.product_id);
        if (info) {
          item.name = info.name || info.label || info.title;
          item.sku = info.sku;
          item.category = info.category;
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
    
    // 🔹 ID produit stocké en attribut HTML masqué (ex: <div class="stock-card" data-product-id="7">)
    card.dataset.productId = item.product_id;

    const name = item.name || `Produit #${item.product_id}`;
    const sku = item.sku || "SKU N/A";
    const category = item.category || "Inconnue";
    const supplier = item.supplier_name || item.supplier || "Inconnu";

    card.innerHTML = `
      <div class="stock-tag">${escapeHtml(sku)}</div>
      <div class="stock-name">
        ${escapeHtml(name)} <small style="opacity: 0.7; font-weight: normal;">(${escapeHtml(sku)})</small>
      </div>
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
    customAlert(`Erreur : ${err.detail || "Impossible d'ajouter le stock."}`);
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
    customAlert(`Erreur : ${err.detail || "Impossible de retirer le stock."}`);
  }
}

// 8. Formulaire d'ajout d'une nouvelle référence (Point 1, 2, 3)
document.getElementById("new-stock-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const idInput = document.getElementById("new-product-id");
  const qtyInput = document.getElementById("new-product-qty");

  const query = idInput.value.trim();
  const quantity = parseInt(qtyInput.value, 10);

  if (!query || !quantity || quantity <= 0) {
    customAlert("Veuillez saisir un identifiant/SKU valide et une quantité strictement positive.");
    return;
  }

  // Résolution du produit par SKU ou ID
  const product = await resolveProductBySkuOrId(query);

  // Point 2 : Le produit n'existe pas
  if (!product) {
    customAlert("Ce produit n'existe pas");
    return;
  }

  // Point 3 : Le produit est discontinued
  if (product.discontinued) {
    customAlert("ce produit ne fait plus partie de notre catalogue il est conservé comme référence pour d'anciennes commandes");
    return;
  }

  // Ajout du stock avec l'ID numérique réel du produit trouvé
  await addStock(product.id, quantity);

  idInput.value = "";
  qtyInput.value = "1";
});


// Configuration de l'URL du Client Web Agent IA
function setupClientWebLink() {
  const aiLink = document.getElementById("ai-agent-link");
  if (!aiLink) return;

  // Récupère l'hôte actuel (localhost ou IP/nom de domaine) et le port configurable
  const host = window.WEB_CLIENT_HOST || window.location.hostname || "localhost";
  const port = window.WEB_CLIENT_PORT || "8080";
  const protocol = window.location.protocol || "http:";

  aiLink.href = `${protocol}//${host}:${port}/index.html`;
}

document.addEventListener("DOMContentLoaded", () => {
  setupClientWebLink();
  init();
});
