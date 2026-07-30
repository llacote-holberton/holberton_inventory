// ============================= COMMON JS ==================================
// Role: fonctions partagées sur l'ensemble des pages du Backoffice.

// ============== 0. CONFIGURATION des appels à l'API Backoffice ============
const BACKOFFICE_API_ROOT = window.location.origin;


// ============== 1. Vérification immédiate de l'authentification ============
async function checkAuth() {
    // 1. Ne rien faire si on est déjà sur la page de login
    if (window.location.pathname.includes("/login")) return;

    const token = localStorage.getItem("token");

    // 2. Si aucun token n'est présent -> redirection immédiate
    if (!token) {
        window.location.href = "/ui/login";
        return;
    }

    try {
        // 3. VÉRIFICATION SÉCURISÉE : On demande au serveur de valider la signature du token
        const response = await fetch("/whoami", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        // Si le serveur rejette le token (falsifié, expiré ou corrompu)
        if (!response.ok) {
            throw new Error("Token invalide ou rejeté par le serveur");
        }

        // Le serveur renvoie le payload certifié par la clé secrète du Backoffice
        const currentUser = await response.json();

        // Extraction sécurisée du rôle et du branch_id
        const role = currentUser.role || "";
        const cleanRole = role.toLowerCase();

        // Mettre à jour le localStorage avec les vraies valeurs du serveur
        localStorage.setItem("role", cleanRole);
        if (currentUser.branch_id !== undefined) {
            localStorage.setItem("branch_id", currentUser.branch_id);
        }

        // 4. Contrôle d'accès à la page Admin
        if (window.location.pathname.includes("/admin") && cleanRole !== "admin") {
            alert(`Accès refusé : réservé aux administrateurs (votre rôle : ${role || "inconnu"}).`);
            window.location.href = "/ui/manager";
        }

    } catch (e) {
        console.warn("Échec d'authentification ou token corrompu :", e);
        // En cas de tentative de bypass / token invalide : nettoyage et expulsion
        localStorage.clear();
        window.location.href = "/ui/login";
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
