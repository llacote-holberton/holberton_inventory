/**
 * Interface Manager (Recherche branches + Gestion stocks).
 * 
 * Endpoints utilisés :
 *  - GET  /search/branches/{pattern}
 *  - GET  /branches/{branch_id}/stocks
 *  - POST /branches/{branch_id}/stock/add
 *  - POST /branches/{branch_id}/stock/remove
 */

const API_BASE = "http://localhost:8000";

let currentBranchId = null;

// Helper d'en-tête pour l'authentification JWT
function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

// -------------------------------------------------------------
// 1. GET /search/branches/{pattern}
// -------------------------------------------------------------
async function searchBranches(pattern) {
  try {
    const response = await fetch(`${API_BASE}/search/branches/${encodeURIComponent(pattern)}`, {
      headers: getAuthHeaders()
    });

    if (response.status === 401) {
      alert("Session expirée. Veuillez vous re-connecter.");
      window.location.href = `${API_BASE}/login.html`;
      return;
    }

    if (!response.ok) throw new Error("Erreur lors de la recherche des branches");

    const branches = await response.json();
    renderBranchResults(branches);
  } catch (error) {
    console.error("Erreur searchBranches:", error);
    alert("Impossible de rechercher les branches.");
  }
}

function renderBranchResults(branches) {
  const container = document.getElementById("branch-results");
  container.innerHTML = "";

  if (branches.length === 0) {
    container.innerHTML = "<p class='empty-msg'>Aucune branche trouvée.</p>";
    return;
  }

  branches.forEach((branch) => {
    const card = document.createElement("div");
    card.className = "branch-card";
    card.textContent = `#${branch.id} - ${branch.name}`;
    card.addEventListener("click", () => selectBranch(branch));
    container.appendChild(card);
  });
}

function selectBranch(branch) {
  currentBranchId = branch.id;
  document.getElementById("current-branch-title").textContent = `Stocks de la branche : ${branch.name} (#${branch.id})`;
  document.getElementById("stock-section").style.display = "block";
  loadBranchStocks(branch.id);
}

// -------------------------------------------------------------
// 2. GET /branches/{branch_id}/stocks
// -------------------------------------------------------------
async function loadBranchStocks(branchId) {
  try {
    const response = await fetch(`${API_BASE}/branches/${branchId}/stocks`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) throw new Error("Erreur lors du chargement des stocks");

    const stocks = await response.json();
    renderStocksTable(stocks);
  } catch (error) {
    console.error("Erreur loadBranchStocks:", error);
    alert("Erreur lors du chargement des stocks.");
  }
}

function renderStocksTable(stocks) {
  const tbody = document.getElementById("stock-table-body");
  tbody.innerHTML = "";

  // Supporte liste d'objets [{item_name, quantity}] ou dictionnaire {item: qty}
  const stockItems = Array.isArray(stocks) 
    ? stocks 
    : Object.entries(stocks).map(([item_name, quantity]) => ({ item_name, quantity }));

  if (stockItems.length === 0) {
    tbody.innerHTML = `<tr><td colspan="2" class="empty-msg">Aucun produit en stock dans cette branche.</td></tr>`;
    return;
  }

  stockItems.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong>${item.item_name || item.name || item.item_id}</strong></td>
      <td>${item.quantity}</td>
    `;
    tbody.appendChild(row);
  });
}

// -------------------------------------------------------------
// 3. POST /branches/{branch_id}/stock/add
// -------------------------------------------------------------
async function addStock() {
  if (!currentBranchId) return;

  const itemName = document.getElementById("item-name").value.trim();
  const quantity = parseInt(document.getElementById("item-quantity").value, 10);

  if (!itemName || isNaN(quantity) || quantity <= 0) {
    alert("Saisie invalide pour le stock.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/branches/${currentBranchId}/stock/add`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ item_name: itemName, quantity: quantity })
    });

    if (response.ok) {
      clearStockForm();
      await loadBranchStocks(currentBranchId);
    } else {
      const err = await response.json().catch(() => ({}));
      alert(err.detail || "Erreur lors de l'ajout du stock.");
    }
  } catch (error) {
    console.error("Erreur addStock:", error);
  }
}

// -------------------------------------------------------------
// 4. POST /branches/{branch_id}/stock/remove
// -------------------------------------------------------------
async function removeStock() {
  if (!currentBranchId) return;

  const itemName = document.getElementById("item-name").value.trim();
  const quantity = parseInt(document.getElementById("item-quantity").value, 10);

  if (!itemName || isNaN(quantity) || quantity <= 0) {
    alert("Saisie invalide pour le retrait du stock.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/branches/${currentBranchId}/stock/remove`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ item_name: itemName, quantity: quantity })
    });

    if (response.ok) {
      clearStockForm();
      await loadBranchStocks(currentBranchId);
    } else {
      const err = await response.json().catch(() => ({}));
      alert(err.detail || "Erreur lors du retrait du stock.");
    }
  } catch (error) {
    console.error("Erreur removeStock:", error);
  }
}

function clearStockForm() {
  document.getElementById("item-name").value = "";
  document.getElementById("item-quantity").value = "";
}

// Event Listeners
document.getElementById("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const pattern = document.getElementById("search-pattern").value.trim();
  if (pattern) searchBranches(pattern);
});

document.getElementById("btn-add-stock").addEventListener("click", addStock);
document.getElementById("btn-remove-stock").addEventListener("click", removeStock);
