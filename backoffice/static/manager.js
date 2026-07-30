/**
 * Interface manager (stock de la branche).
 *
 */

let userBranchId = null;
let stockData = [];
const stockListEl = document.getElementById("stock-list");

// ============== 1. Initializing page (checks auth+loaduserinfo+stocks) ===================
async function init() {
  checkAuth();

  // Bouton de déconnexion
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.clear();
      window.location.href = "/ui/login";
    });
  }

  // Récupération des infos du manager pour obtenir son branch_id
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

// ============== 2. Provides a fetch wrapper automate token injection in requests ===================
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

// ============== 3. Generates the list of products in stock ===================
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
    card.innerHTML = `
      <div class="stock-tag">#${item.product_id}</div>
      <div class="stock-name">Produit #${item.product_id}</div>
      <div class="stock-qty">
        <span class="current ${item.quantity === 0 ? "zero" : ""}">Quantité actuelle : ${item.quantity}</span>
        <input type="number" min="1" value="1" aria-label="Quantité à ajuster pour le produit #${item.product_id}">
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

// async function adjustStock(productId, amount, action) {
//   const endpoint = `/branches/${currentBranchId}/stock/${action}`;
//   
//   const response = await apiFetch(endpoint, {
//     method: "POST",
//     body: JSON.stringify({
//       product_id: productId,
//       amount: amount
//     })
//   });
// 
//   if (!response) return;
// 
//   if (response.ok) {
//     await loadStocks(); // Rechargement simple et propre de la liste
//   } else {
//     const errorData = await response.json();
//     alert(`Erreur : ${errorData.detail || "Opération impossible"}`);
//   }
// }

// ============== 4a. Send stock change instruction - Add ===================
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

// ============== 4b. Send stock change instruction - Remove ===================
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

// ============== 5. Loading stock data from db API ===================
async function loadStock() {
  if (!userBranchId) return;

  try {
    const response = await apiFetch(`/branches/${userBranchId}/stocks`);
    if (!response || !response.ok) {
      throw new Error(`Statut HTTP ${response?.status}`);
    }
    stockData = await response.json();
    renderStock();
  } catch (error) {
    console.error("Erreur de chargement des stocks:", error);
    if (stockListEl) {
      stockListEl.innerHTML = `<p class="placeholder">Erreur lors du chargement des stocks.</p>`;
    }
  }
}

// Superceded by the function below directly in form listener.
// function addNewProductStock(productId, quantity) {
//   const existing = stockData.find((p) => p.id === productId);
//   if (existing) {
//     // Le produit est déjà en stock dans cette branche : on incrémente au
//     // lieu de créer une deuxième ligne pour le même produit.
//     adjustStock(productId, quantity);
//     return;
//   }
// 
//   // TODO : en vrai, le Backoffice doit d'abord vérifier que ce produit
//   // existe réellement (via l'API Produit, à travers le serveur MCP ou un
//   // appel direct côté Backoffice) avant de créer une ligne de stock, et
//   // renvoyer nom/catégorie/fournisseur depuis cette vérification plutôt
//   // que depuis un catalogue local comme ici.
//   const catalogEntry = MOCK_CATALOG[productId] || {
//     name: `Produit #${productId} (non reconnu en mode mock)`,
//     category: "Inconnue",
//     supplier: "Inconnu",
//   };
// 
//   stockData.push({ id: productId, quantity, ...catalogEntry });
//   renderStock();
// }

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

  // Envoie la requête d'ajout directement à l'API backend
  await addStock(productId, quantity);

  idInput.value = "";
  qtyInput.value = "1";
});

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

document.addEventListener("DOMContentLoaded", init);
