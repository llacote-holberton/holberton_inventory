const AI_SERVICE_BASE = "http://localhost:8003";

const form = document.getElementById("chat-form");
const questionField = document.getElementById("question");
const responseBox = document.getElementById("response-box");

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = questionField.value.trim();
  if (!question) return;

  responseBox.classList.remove("error");
  responseBox.textContent = "";

  const url = `${AI_SERVICE_BASE}/ask/stream?question=${encodeURIComponent(question)}`;
  const source = new EventSource(url);

  source.onmessage = (event) => {
    responseBox.textContent += event.data;
  };

  source.addEventListener("done", () => {
    source.close();
  });

  source.onerror = () => {
    source.close();
    if (!responseBox.textContent) {
      responseBox.textContent = "Le service est momentanément indisponible. Réessaie dans un instant.";
      responseBox.classList.add("error");
    }
  };
});
