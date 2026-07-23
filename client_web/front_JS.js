// Le client web appelle directement l'AI Query Service en REST (voir
// justification REST vs WebSocket dans ai_service/main.py).
const AI_SERVICE_BASE = "http://localhost:8002";
const AI_SERVICE_URL = `${AI_SERVICE_BASE}/ask`;

// Variante streaming (SSE), à utiliser à la place de askQuestion() ci-dessous
// si on veut afficher la réponse au fur et à mesure au lieu d'attendre le
// texte complet. EventSource ne fait que du GET : la question passe en
// paramètre d'URL.
function askQuestionStream(question, botBubble) {
  const url = `${AI_SERVICE_BASE}/ask/stream?question=${encodeURIComponent(question)}`;
  const source = new EventSource(url);

  source.onmessage = (event) => {
    botBubble.textContent += event.data;
    messages.scrollTop = messages.scrollHeight;
  };

  source.addEventListener("done", () => {
    source.close();
  });

  source.onerror = () => {
    // EventSource retente automatiquement en cas de coupure ; ici on
    // préfère fermer proprement et afficher une erreur.
    source.close();
    if (!botBubble.textContent) {
      botBubble.textContent = "Erreur : flux interrompu.";
      botBubble.classList.add("error");
    }
  };
}

const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const messages = document.getElementById("messages");

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  addMessage(question, "user");
  input.value = "";
  const loadingBubble = addMessage("...", "bot loading");

  try {
    const response = await fetch(AI_SERVICE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Statut HTTP ${response.status}`);
    }

    const data = await response.json();
    loadingBubble.remove();
    addMessage(data.answer, "bot");
  } catch (error) {
    loadingBubble.remove();
    addMessage("Erreur : impossible de contacter le service IA.", "bot error");
  }
});
