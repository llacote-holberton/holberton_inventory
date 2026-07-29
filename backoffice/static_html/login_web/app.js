// LOGIN FORM MANAGEMENT FROM GEMINI
// ⚙️ CONFIGURATION : Endpoint API de connexion
    const LOGIN_API_URL = "http://localhost:8000/login";

    document.getElementById("login-form").addEventListener("submit", async (event) => {
      event.preventDefault();

      const errorEl = document.getElementById("error-msg");
      errorEl.style.display = "none";
      errorEl.textContent = "";

      // 🔍 3. Contrôles de sécurité & nettoyage basique
      const rawUsername = document.getElementById("username").value;
      const rawPassword = document.getElementById("password").value;

      // a) Nettoyage des espaces superflus (Trim)
      const username = rawUsername.trim();
      const password = rawPassword;

      // b) Vérification des champs non vides
      if (!username || !password) {
        showError("Veuillez remplir tous les champs.");
        return;
      }

      // c) Contrôle de longueur minimale
      if (username.length < 3) {
        showError("Le nom d'utilisateur doit faire au moins 3 caractères.");
        return;
      }
      if (password.length < 4) {
        showError("Le mot de passe doit faire au moins 4 caractères.");
        return;
      }

      // d) Neutralisation basique de caractères dangereux sur le username (XSS/Injection)
      const sanitizedUsername = sanitizeInput(username);

      // 📤 2. Envoi du corps JSON exact
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
          
          // Stockage du token reçu
          if (data.access_token || data.token) {
            localStorage.setItem("access_token", data.access_token || data.token);
          }

          // Redirection vers le panneau d'administration du backoffice
          window.location.href = "http://localhost:8000/ui/admin";
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
