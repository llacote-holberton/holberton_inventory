import os
import uuid

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://product_mcp_server:8001/mcp")

# Avec Gemini, pas besoin de LiteLlm : c'est le modèle natif d'ADK, on
# passe directement le nom du modèle en chaîne de caractères. Nécessite
# les variables d'environnement GOOGLE_API_KEY et
# GOOGLE_GENAI_USE_VERTEXAI=FALSE (pour utiliser l'API Google AI Studio
# plutôt que Vertex AI).
MODEL = "gemini-2.5-flash"

APP_NAME = "ai_query_service"

SYSTEM_PROMPT = (
    "Tu es un assistant qui répond à des questions sur des produits et du "
    "stock en te basant UNIQUEMENT sur les informations renvoyées par les "
    "outils disponibles. Si les outils ne fournissent pas assez "
    "d'informations pour répondre avec certitude, dis explicitement que "
    "l'information n'est pas disponible. N'invente jamais de données "
    "(prix, quantités, noms de produits, etc.)."
)

# Le toolset se connecte au serveur MCP en streamable-http (le même
# transport que celui utilisé côté serveur dans product_mcp_server/server.py).
_mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL),
)

root_agent = LlmAgent(
    model=MODEL,
    name="product_stock_agent",
    instruction=SYSTEM_PROMPT,
    tools=[_mcp_toolset],
)

_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)


async def answer_question(question: str) -> str:
    """
    Traite une question de façon totalement indépendante : on crée une
    session ADK jetable (un identifiant unique par appel), on l'utilise
    une fois, puis on ne la réutilise jamais. Cohérent avec l'énoncé qui
    précise qu'aucun historique de conversation n'est requis.
    """
    user_id = "anonymous"
    session_id = str(uuid.uuid4())

    await _session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=question)])

    final_text = "Je n'ai pas réussi à obtenir une réponse fiable, réessaie ta question."
    async for event in _runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text for part in event.content.parts if part.text
            )

    return final_text


async def answer_question_stream(question: str):
    """
    Variante streaming : le Runner d'ADK émet des events au fur et à
    mesure (y compris des deltas de texte partiels avant l'event final).
    On ne renvoie que le texte, morceau par morceau, à l'appelant (qui
    s'en sert pour alimenter le flux SSE dans main.py).
    """
    user_id = "anonymous"
    session_id = str(uuid.uuid4())

    await _session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=question)])

    async for event in _runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    yield part.text
