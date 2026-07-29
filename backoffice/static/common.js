// ============================= COMMON JS ==================================
// Role: fonctions partagées sur l'ensemble des pages du Backoffice.

// ============== 0. CONFIGURATION des appels à l'API Backoffice ============
const BACKOFFICE_API_ROOT = window.location.origin;


// ============== 1. Vérification immédiate de l'authentification ============
function checkAuth() {
    if (window.location.pathname.includes("/login")) return;

    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/ui/login";
        return;
    }

    // Récupérer le rôle (localStorage ou directement depuis le token JWT)
    let role = localStorage.getItem("role");

    if (!role && token) {
        try {
            const payload = JSON.parse(atob(token.split(".")[1]));
            role = payload.role;
            if (role) localStorage.setItem("role", role);
        } catch (e) {
            console.error("Impossible de lire le rôle depuis le token", e);
        }
    }

    // Formatage en minuscules pour éviter les pièges ("ADMIN" vs "admin")
    const cleanRole = (role || "").toLowerCase();

    // Vérification de l'accès Admin
    if (window.location.pathname.includes("/admin") && cleanRole !== "admin") {
        alert(`Accès refusé : réservé aux administrateurs (votre rôle : ${role || "inconnu"}).`);
        window.location.href = "/ui/manager";
    }
}

// Exécuté immédiatement au chargement du script
checkAuth();


// ============== 2. Injection automatique du Header et Footer ==============
document.addEventListener("DOMContentLoaded", () => {
    renderHeader();
    renderFooter();
});

function renderHeader() {
    const headerContainer = document.getElementById("header-container");
    if (!headerContainer) return;

    const role = localStorage.getItem("role") || "Utilisateur";

    headerContainer.innerHTML = `
        <header style="display:flex; justify-content:space-between; align-items:center; padding: 10px 20px; background: #1e293b; color: white;">
            <div class="logo"><strong>Holberton Inventory</strong></div>
            <nav style="display:flex; align-items:center; gap: 15px;">
                <span>Rôle: <strong>${role}</strong></span>
                <button onclick="logout()" style="padding: 5px 10px; cursor: pointer; background: #ef4444; color: white; border: none; border-radius: 4px;">Déconnexion</button>
            </nav>
        </header>
    `;
}

function renderFooter() {
    const footerContainer = document.getElementById("footer-container");
    if (!footerContainer) return;

    footerContainer.innerHTML = `
        <footer style="text-align: center; padding: 15px; margin-top: 30px; border-top: 1px solid #ccc; font-size: 0.9em; color: #666;">
            <p>&copy; 2026 Holberton Inventory - Projet Backoffice</p>
        </footer>
    `;
}


// ============== 3. Action de déconnexion ===================================
function logout() {
    localStorage.clear();
    window.location.href = "/ui/login";
}


// ============== 4. Wrapper Fetch (ajoute automatiquement le Bearer token) ==
async function apiFetch(url, options = {}) {
    const token = localStorage.getItem("token");
    
    // Si l'URL passée est relative (ex: "/branches"), on lui préfixe la racine
    const fullUrl = url.startsWith("http") ? url : `${BACKOFFICE_API_ROOT}${url}`;

    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
    };

    const response = await fetch(fullUrl, options);

    if (response.status === 401) {
        localStorage.clear();
        window.location.href = "/ui/login";
        return;
    }

    return response;
}
