/**
 * Interface admin (branches + utilisateurs).
 *
 * TODO (une fois l'API admin du Backoffice prête côté binôme) :
 *   - Remplacer BRANCH_API_URL / USER_API_URL par les vrais endpoints
 *   - Envoyer le token d'authentification admin (header Authorization)
 *   - Remplacer chaque fonction create/delete/update ci-dessous par un
 *     vrai appel fetch (POST/PATCH/DELETE) vers le Backoffice
 *   - Le changement de mot de passe utilise window.prompt() ici pour
 *     rester simple en mode mock ; remplacer par un vrai formulaire
 *     (avec confirmation, règles de complexité, etc.) une fois branché.
 *   - Retirer MOCK_BRANCHES / MOCK_USERS : données de démonstration
 *     uniquement, pour visualiser l'interface avant que le Backoffice
 *     soit prêt.
 *
 * Rappel de la consigne : l'admin ne gère jamais le stock, seulement les
 * utilisateurs et leur affectation à une branche.
 */

const BRANCH_API_URL = "http://localhost:8000/api/branches";
const USER_API_URL = "http://localhost:8000/api/users";


const MOCK_BRANCHES = [
  { id: 1, name: "Lyon Part-Dieu" },
  { id: 2, name: "Paris Bastille" },
];

const MOCK_USERS = [
  { id: 1, username: "j.martin", branch_id: 1, active: true },
  { id: 2, username: "s.durand", branch_id: 2, active: true },
  { id: 3, username: "k.benali", branch_id: 1, active: false },
];

let branches = [];
let users = [];
let nextBranchId = 1;
let nextUserId = 1;

const branchListEl = document.getElementById("branch-list");
const userListEl = document.getElementById("user-list");
const userBranchSelect = document.getElementById("user-branch");

function branchName(branchId) {
  const branch = branches.find((b) => b.id === branchId);
  return branch ? branch.name : "—";
}

function renderBranchSelect() {
  userBranchSelect.innerHTML = branches
    .map((b) => `<option value="${b.id}">${b.name}</option>`)
    .join("");
}

function renderBranches() {
  if (!branchListEl) return;
  branchListEl.innerHTML = "";
  branches.forEach((branch) => {
    const chip = document.createElement("div");
    chip.className = "branch-chip";
    chip.innerHTML = `
      <span class="tag">#${branch.id}</span>
      <span>${branch.name || branch.label}</span>
      <button type="button" disabled style="opacity:0.4; cursor:not-allowed;" title="Non disponible dans cette version">✕</button>
    `;
    branchListEl.appendChild(chip);
  });
  renderBranchSelect();
}

function renderUsers() {
  if (!userListEl) return;
  userListEl.innerHTML = "";

  users.forEach((user) => {
    const row = document.createElement("div");
    row.className = `user-row ${user.is_active ? "" : "inactive"}`;

    // 1. Condition sur le rôle pour l'affichage de la branche
    let branchHtml = "";

    if (user.role === "admin") {
      // Pour les admins : pas de menu déroulant, juste un texte explicite
      branchHtml = `<span class="no-branch" style="color: #888; font-style: italic;">N/A (Admin)</span>`;
    } else {
      // Pour les managers : menu déroulant avec sélection de leur branche
      const branchOptions = branches
        .map((b) => `<option value="${b.id}" ${b.id === user.branch_id ? "selected" : ""}>${b.label}</option>`)
        .join("");

      branchHtml = `<select aria-label="Branche assignée à ${user.name}">${branchOptions}</select>`;
    }

    row.innerHTML = `
      <span class="username">${user.name} (${user.role})</span>
      <span class="status-badge ${user.is_active ? "active" : "inactive"}">
        ${user.is_active ? "Actif" : "Désactivé"}
      </span>
      ${branchHtml}
      <div class="actions">
        <button type="button" class="pwd-btn">Changer mot de passe</button>
        <button type="button" class="toggle-btn ${user.is_active ? "deactivate" : "reactivate"}">
          ${user.is_active ? "Désactiver" : "Réactiver"}
        </button>
      </div>
    `;

    // 2. Événement de changement de branche uniquement si le menu déroulant existe (managers)
    const selectEl = row.querySelector("select");
    if (selectEl) {
      selectEl.addEventListener("change", (e) => {
        const newBranchId = parseInt(e.target.value, 10);
        changeUserBranch(user.id, newBranchId, user.branch_id);
      });
    }

    // Événements communs
    row.querySelector(".pwd-btn").addEventListener("click", () => {
      changeUserPassword(user.id);
    });
    row.querySelector(".toggle-btn").addEventListener("click", () => {
      toggleUserActive(user.id, user.is_active);
    });

    userListEl.appendChild(row);
  });
}

/* COMMENTED FOR DEMO
function createBranch(name) {
  // TODO : POST vers BRANCH_API_URL, puis utiliser l'id renvoyé par le
  // Backoffice au lieu de nextBranchId généré côté client.
  branches.push({ id: nextBranchId++, name });
  renderBranches();
  renderUsers();
}

function deleteBranch(branchId) {
  const affectedUsers = users.filter((u) => u.branch_id === branchId);
  if (affectedUsers.length > 0) {
    const confirmed = confirm(
      `${affectedUsers.length} utilisateur(s) sont assignés à cette branche. Supprimer quand même ?`
    );
    if (!confirmed) return;
  }
  // TODO : DELETE vers BRANCH_API_URL/{branchId}
  branches = branches.filter((b) => b.id !== branchId);
  renderBranches();
  renderUsers();
}
*/

function createUser(username, password, branchId) {
  // TODO : POST vers USER_API_URL avec { username, password, branch_id }.
  // Le mot de passe ne doit JAMAIS être stocké/affiché en clair côté
  // Backoffice : le hashage se fait côté serveur, jamais dans ce JS.
  users.push({ id: nextUserId++, username, branch_id: branchId, active: true });
  renderUsers();
}

async function changeUserBranch(userId, newBranchId, oldBranchId) {
  // Si l'utilisateur réactive la même branche, on ne fait rien
  if (newBranchId === oldBranchId) return;

  const res = await apiFetch(`/users/${userId}/assign_branch`, {
    method: "POST",
    body: JSON.stringify({ branch_id: newBranchId })
  });

  if (res && res.ok) {
    alert("Branche réaffectée avec succès !");
    loadData(); // Synchronise l'interface
  } else {
    alert("Erreur : Impossible de réaffecter la branche.");
    loadData(); // Remet le menu déroulant sur l'ancienne valeur en cas d'échec
  }
}

// Changer le mot de passe
async function changeUserPassword(userId) {
  const newPassword = prompt("Saisissez le nouveau mot de passe :");
  if (!newPassword || newPassword.trim().length < 4) {
    alert("Le mot de passe doit contenir au moins 4 caractères.");
    return;
  }

  const res = await apiFetch(`/users/${userId}/reset_password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword.trim() })
  });

  if (res && res.ok) {
    alert("Mot de passe mis à jour avec succès !");
  } else {
    alert("Échec de la modification du mot de passe.");
  }
}

async function toggleUserActive(userId, currentStatus) {
  const endpoint = currentStatus 
    ? `/users/${userId}/deactivate` 
    : `/users/${userId}/activate`;

  const res = await apiFetch(endpoint, { method: "POST" });

  if (res && res.ok) {
    loadData();
  } else {
    alert("Impossible de modifier le statut de l'utilisateur.");
  }
}

async function loadData() {
  try {
    // Recommandé : appels parallèles sécurisés via apiFetch
    const [branchResp, userResp] = await Promise.all([
      apiFetch("/branches"),
      apiFetch("/users")
    ]);

    if (!branchResp.ok || !userResp.ok) {
      alert("Erreur lors de la récupération des données.");
      return;
    }

    branches = await branchResp.json();
    users = await userResp.json();

    renderBranches();
    renderUsers();
  } catch (error) {
    console.error("Erreur serveur :", error);
  }
}

document.getElementById("branch-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.getElementById("branch-name");
  const name = input.value.trim();
  if (!name) return;
  createBranch(name);
  input.value = "";
});

document.getElementById("user-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const usernameInput = document.getElementById("user-username");
  const passwordInput = document.getElementById("user-password");
  const username = usernameInput.value.trim();
  const password = passwordInput.value;
  const branchId = parseInt(userBranchSelect.value, 10);
  if (!username || !password || !branchId) return;
  createUser(username, password, branchId);
  usernameInput.value = "";
  passwordInput.value = "";
});

loadData();
