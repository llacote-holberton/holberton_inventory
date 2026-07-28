from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import answer_question, answer_question_stream

app = FastAPI(title="AI Query Service")

# En dev on ouvre le CORS pour que le client_web (servi sur un autre port)
# puisse appeler l'API directement depuis le navigateur.
# "GET" est nécessaire en plus de "POST" pour /ask/stream, car EventSource
# (l'API navigateur qui consomme du SSE) ne peut faire que des requêtes GET.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _format_sse_event(data: str) -> str:
    """
    Met une chaîne au format attendu par le protocole SSE : chaque ligne du
    message doit être préfixée par "data: ", et le message se termine par
    une ligne vide. Nécessaire si le morceau de texte contient lui-même des
    retours à la ligne.
    """
    lines = data.split("\n")
    return "".join(f"data: {line}\n" for line in lines) + "\n"


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
async def ask(payload: Question):
    answer = await answer_question(payload.question)
    return Answer(answer=answer)


@app.get("/ask/stream")
async def ask_stream(question: str):
    """
    Version SSE de /ask. En GET (et pas POST) car EventSource, l'API
    navigateur standard pour consommer du SSE, ne supporte que GET et ne
    permet pas d'envoyer de corps de requête : la question passe donc en
    paramètre d'URL (?question=...).
    """

    async def event_generator():
        async for chunk in answer_question_stream(question):
            yield _format_sse_event(chunk)
        # Événement nommé "done" : permet au client de savoir que le flux
        # est terminé sans devoir attendre la fermeture de la connexion.
        yield "event: done\ndata: end\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
