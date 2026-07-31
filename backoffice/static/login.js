// ⚙️ CONFIGURATION : Hôte de l'API (se réfère dynamiquement au domaine courant)
const BASE_HOST = window.location.origin; // ex: "http://localhost:8000"
const LOGIN_API_URL = `${BASE_HOST}/login`;

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const errorEl = document.getElementById("error-msg");
  errorEl.style.display = "none";
  errorEl.textContent = "";

  // 🔍 1. Contrôles de sécurité & nettoyage
  const rawUsername = document.getElementById("username").value;
  const rawPassword = document.getElementById("password").value;

  const username = rawUsername.trim();
  const password = rawPassword;

  if (!username || !password) {
    showError("Veuillez remplir tous les champs.");
    return;
  }

  if (username.length < 3) {
    showError("Le nom d'utilisateur doit faire au moins 3 caractères.");
    return;
  }
  if (password.length < 4) {
    showError("Le mot de passe doit faire au moins 4 caractères.");
    return;
  }

  const sanitizedUsername = sanitizeInput(username);

  // 📤 2. Envoi des identifiants
  const payload = {
    username: sanitizedUsername,
    password: password
  };

  try {
    const response = await fetch(LOGIN_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      const data = await response.json();
      const token = data.access_token || data.token;

      if (token) {
        // Stockage du jeton
        localStorage.setItem("token", token);

        // 🔍 3. Décodage du payload JWT pour lire le rôle
        try {
          const payloadBase64 = token.split(".")[1]; // Deuxième partie du JWT
          const decodedPayload = JSON.parse(atob(payloadBase64));
          const role = decodedPayload.role;

          localStorage.setItem("role", role);

          // 🔀 4. Redirection selon le rôle
          if (role === "admin") {
            window.location.href = `${BASE_HOST}/ui/admin`;
          } else if (role === "manager") {
            window.location.href = `${BASE_HOST}/ui/manager`;
          } else {
            showError(`Rôle inconnu (${role}). Redirection impossible.`);
          }
        } catch (e) {
          console.error("Erreur de décodage du token :", e);
          showError("Format de jeton invalide reçu du serveur.");
        }
      } else {
        showError("Aucun jeton n'a été renvoyé par le serveur.");
      }
    } else {
      const errData = await response.json().catch(() => ({}));
      showError(errData.detail || "Identifiants incorrects.");
    }
  } catch (error) {
    console.error("Erreur d'authentification :", error);
    showError("Impossible de contacter le serveur d'authentification.");
  }
});

function showError(message) {
  const errorEl = document.getElementById("error-msg");
  errorEl.textContent = message;
  errorEl.style.display = "block";
}

// Fonction de nettoyage anti-XSS basique
function sanitizeInput(str) {
  return str.replace(/[<>&"']/g, "");
}
