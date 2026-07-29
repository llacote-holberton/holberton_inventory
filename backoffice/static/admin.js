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
  branchListEl.innerHTML = "";
  branches.forEach((branch) => {
    const chip = document.createElement("div");
    chip.className = "branch-chip";
    chip.innerHTML = `
      <span class="tag">#${branch.id}</span>
      <span>${branch.name}</span>
      <button type="button" aria-label="Supprimer la branche ${branch.name}">✕</button>
    `;
    chip.querySelector("button").addEventListener("click", () => deleteBranch(branch.id));
    branchListEl.appendChild(chip);
  });
  renderBranchSelect();
}

function renderUsers() {
  userListEl.innerHTML = "";
  users.forEach((user) => {
    const row = document.createElement("div");
    row.className = `user-row ${user.active ? "" : "inactive"}`;

    const branchOptions = branches
      .map((b) => `<option value="${b.id}" ${b.id === user.branch_id ? "selected" : ""}>${b.name}</option>`)
      .join("");

    row.innerHTML = `
      <span class="username">${user.username}</span>
      <span class="status-badge ${user.active ? "active" : "inactive"}">${user.active ? "Actif" : "Désactivé"}</span>
      <select aria-label="Branche assignée à ${user.username}">${branchOptions}</select>
      <div class="actions">
        <button type="button" class="pwd-btn">Changer mot de passe</button>
        <button type="button" class="toggle-btn ${user.active ? "deactivate" : "reactivate"}">
          ${user.active ? "Désactiver" : "Réactiver"}
        </button>
      </div>
    `;

    row.querySelector("select").addEventListener("change", (event) => {
      changeUserBranch(user.id, parseInt(event.target.value, 10));
    });
    row.querySelector(".pwd-btn").addEventListener("click", () => changeUserPassword(user.id));
    row.querySelector(".toggle-btn").addEventListener("click", () => toggleUserActive(user.id));

    userListEl.appendChild(row);
  });
}

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

function createUser(username, password, branchId) {
  // TODO : POST vers USER_API_URL avec { username, password, branch_id }.
  // Le mot de passe ne doit JAMAIS être stocké/affiché en clair côté
  // Backoffice : le hashage se fait côté serveur, jamais dans ce JS.
  users.push({ id: nextUserId++, username, branch_id: branchId, active: true });
  renderUsers();
}

function changeUserBranch(userId, branchId) {
  // TODO : PATCH vers USER_API_URL/{userId} avec { branch_id: branchId }
  const user = users.find((u) => u.id === userId);
  if (user) user.branch_id = branchId;
}

function changeUserPassword(userId) {
  const newPassword = prompt("Nouveau mot de passe pour cet utilisateur :");
  if (!newPassword) return;
  // TODO : PATCH vers USER_API_URL/{userId}/password avec { password: newPassword }
  alert("Mot de passe mis à jour (simulation — aucune donnée envoyée pour l'instant).");
}

function toggleUserActive(userId) {
  // TODO : PATCH vers USER_API_URL/{userId} avec { active: !user.active }
  // (soft-delete : on désactive, on ne supprime jamais la ligne)
  const user = users.find((u) => u.id === userId);
  if (user) user.active = !user.active;
  renderUsers();
}

async function loadData() {
  try {
    const [branchResp, userResp] = await Promise.all([
      fetch(BRANCH_API_URL),
      fetch(USER_API_URL),
    ]);
    if (!branchResp.ok || !userResp.ok) throw new Error("Statut HTTP inattendu");
    branches = await branchResp.json();
    users = await userResp.json();
  } catch (error) {
    // Le Backoffice n'est pas encore prêt : données de démonstration.
    branches = MOCK_BRANCHES;
    users = MOCK_USERS;
  }
  nextBranchId = Math.max(0, ...branches.map((b) => b.id)) + 1;
  nextUserId = Math.max(0, ...users.map((u) => u.id)) + 1;
  renderBranches();
  renderUsers();
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
