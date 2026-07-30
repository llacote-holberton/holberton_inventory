const AI_SERVICE_BASE = "http://localhost:8003";

const form = document.getElementById("chat-form");
const questionField = document.getElementById("question");
const responseBox = document.getElementById("response-box");
const submitBtn = form.querySelector("button[type='submit']");
const loadingMsg = document.getElementById("loading-msg");

let currentSource = null;

function setupLoginLink() {
  const loginLink = document.getElementById("login-link");
  if (!loginLink) return;

  const host = window.BACKOFFICE_HOST || window.location.hostname || "localhost";
  const port = window.BACKOFFICE_PORT || "8000";
  const protocol = window.location.protocol || "http:";

  loginLink.href = `${protocol}//${host}:${port}/ui/login`;
}

// S'exécute immédiatement SI le DOM est déjà prêt, sinon attend le DOMContentLoaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupLoginLink);
} else {
  setupLoginLink();
}

// Gestion des touches Entrée et Shift+Entrée
questionField.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault(); // Évite le saut de ligne non désiré
    if (!submitBtn.disabled) {
      form.requestSubmit(); // Déclenche l'événement submit du formulaire
    }
  }
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = questionField.value.trim();
  if (!question) return;

  // 1. Fermer une éventuelle connexion SSE précédente encore active
  if (currentSource) {
    currentSource.close();
  }

  // 2. Préparer l'interface (réinitialiser la boîte de réponse)
  responseBox.classList.remove("error");
  responseBox.textContent = "";

  // 3. Verrouiller les champs et afficher le message d'attente
  questionField.disabled = true;
  submitBtn.disabled = true;
  submitBtn.textContent = "Recherche...";
  if (loadingMsg) loadingMsg.hidden = false;

  const url = `${AI_SERVICE_BASE}/ask/stream?question=${encodeURIComponent(question)}`;
  currentSource = new EventSource(url);

  // 4. Réception des morceaux de réponse (stream)
  currentSource.onmessage = (event) => {
    responseBox.textContent += event.data;
  };

  // 5. Fin de la réponse signalée par le serveur (événement nommé "done")
  currentSource.addEventListener("done", () => {
    cleanup();
  });

  // 6. Gestion des erreurs de connexion
  currentSource.onerror = () => {
    cleanup();
    if (!responseBox.textContent) {
      responseBox.textContent = "Le service est momentanément indisponible. Réessaie dans un instant.";
      responseBox.classList.add("error");
    }
  };

  // Restaure l'état du formulaire et masque le message d'attente
  function cleanup() {
    if (currentSource) {
      currentSource.close();
      currentSource = null;
    }
    questionField.disabled = false;
    submitBtn.disabled = false;
    submitBtn.textContent = "Envoyer";
    if (loadingMsg) loadingMsg.hidden = true;
    questionField.focus();
  }
});

