import os
import uuid

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://product_mcp_server:8001/mcp")

# Format attendu par LiteLLM pour Groq : "groq/<nom_du_modele>".
# llama-3.3-70b-versatile plutôt qu'un modèle "openai/gpt-oss-*" :
# ces derniers sont des modèles "reasoning", et LiteLLM a un bug connu
# et non résolu (issues ouvertes sur son propre dépôt GitHub) où le
# contenu de raisonnement est réinjecté dans l'historique reconstruit
# pour l'appel suivant, ce que l'API Groq rejette ensuite -- ça casse
# précisément dans une boucle multi-tours comme la nôtre (question ->
# appel de tool -> réponse). llama-3.3-70b-versatile n'a pas cette classe
# de bug puisque ce n'est pas un modèle "reasoning".
MODEL = "groq/llama-3.3-70b-versatile"
APP_NAME = "ai_query_service"

SYSTEM_PROMPT = (
    "Tu es un assistant qui répond à des questions sur des produits et du "
    "stock en te basant UNIQUEMENT sur les informations renvoyées par les "
    "outils disponibles. Si les outils ne fournissent pas assez "
    "d'informations pour répondre avec certitude, dis explicitement que "
    "l'information n'est pas disponible. N'invente jamais de données "
    "(prix, quantités, noms de produits, etc.).\n\n"
    "RÈGLE STRICTE SUR L'USAGE DES OUTILS : dès qu'une question porte sur "
    "des produits ou du stock, appelle IMMÉDIATEMENT l'outil pertinent "
    "dans ta réponse, sans jamais décrire d'abord ce que tu comptes "
    "faire et sans demander de précisions avant d'avoir essayé. Par "
    "exemple, pour \"liste-moi les produits disponibles\", appelle "
    "list_products tout de suite, sans filtre si aucun n'est précisé, "
    "au lieu d'expliquer que tu pourrais l'utiliser ou de demander des "
    "critères de recherche au préalable. Ne dis jamais des phrases comme "
    "\"je vais utiliser l'outil X\" ou \"je peux essayer d'utiliser Y\" "
    "sans l'appeler réellement dans le même tour. Ne demande des "
    "précisions à l'utilisateur qu'APRÈS avoir essayé les outils et "
    "constaté que leur résultat est réellement insuffisant.\n\n"
    "IMPORTANT : le catalogue de produits (noms, descriptions, tags) est "
    "entièrement en anglais, même si l'utilisateur pose sa question en "
    "français. Quand tu utilises le paramètre de recherche texte (q) du "
    "tool list_products, traduis d'abord les mots-clés pertinents en "
    "anglais (ex. \"souris sans fil\" -> \"wireless mouse\"), car la "
    "recherche est un filtre texte brut qui ne traduit rien lui-même. Ne "
    "traduis en revanche jamais les noms de produits dans ta réponse "
    "finale à l'utilisateur : garde-les tels que renvoyés par le "
    "catalogue."
)
# Le toolset se connecte au serveur MCP en streamable-http (le même
# transport que celui utilisé côté serveur dans product_mcp_server/server.py).
# Point important : les tools et leurs schémas sont récupérés dynamiquement
# auprès du serveur MCP — un changement de signature côté server.py (comme
# le passage de `product_id` à `id_or_sku` pour get_product_details) n'a
# donc rien à modifier ici.
_mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL),
)

root_agent = LlmAgent(
    # temperature=0 : recommandation officielle de Groq pour l'erreur
    # "tool_use_failed" — une température plus basse rend le format de
    # l'appel de fonction plus déterministe, donc moins sujet à un
    # mélange de texte libre et de syntaxe de tool mal formée.
    model=LiteLlm(model=MODEL, temperature=0),
    name="product_stock_agent",
    instruction=SYSTEM_PROMPT,
    tools=[_mcp_toolset],
)

_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)


async def answer_question(question: str) -> str:
    """
    Traite une question de façon totalement indépendante : on crée une
    session ADK jetable (un identifiant unique par appel), utilisée une
    seule fois. Cohérent avec l'énoncé qui précise qu'aucun historique de
    conversation n'est requis.
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