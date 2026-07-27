import os
import uuid

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://product_mcp_server:8001/mcp")

# Format attendu par LiteLLM pour NVIDIA NIM : "nvidia_nim/<org>/<modele>".
# minimaxai/minimax-m3 : minimax-m2.7 a atteint sa fin de vie le
# 27 juillet 2026 (retiré du catalogue NVIDIA) ; m3 est son successeur,
# disponible en free endpoint, avec tool-calling supporté.
MODEL = "nvidia_nim/minimaxai/minimax-m3"
APP_NAME = "ai_query_service"

SYSTEM_PROMPT = """
Tu es un assistant qui interroge des APIs pour répondre à des questions
  sur des produits et leurs stocks correspondant dans des boutiques (branches).
Note que si les questions peuvent être en français, le catalogue et les API
  sont en anglais. Tu dois donc si besoin traduire préalablement les mots-clés
  relatifs aux informations produits (SAUF le nom du fournisseur et le sku)
  pour mieux interroger les APIs.
Tu dois aussi absolument respecter toutes ces contraintes.
- Ne détaille jamais ton raisonnement. Seule la réponse finale doit apparaître.
- Dès qu'une question porte sur des produits ou du stock, appelle IMMÉDIATEMENT
  l'outil pertinent, sans jamais décrire d'abord ce que tu comptes faire et
  sans demander de précisions avant d'avoir essayé.
- get_stock exige un branch_id numérique. Si la question mentionne une
  branche par son nom (ex. "Lyon Part-Dieu"), appelle d'abord list_branches
  pour trouver le bon id avant d'appeler get_stock.
- Quand tu utilises tes outils pour ton raisonnement traduis en anglais les noms des produits.
- Si un élement de la question est 'invalide' (magasin ou produit inexistant) dis-le immédiatement.
- RÈGLE ABSOLUE : ta réponse finale doit TOUJOURS être dans la même langue que
  la question posée, quelle qu'elle soit (français, anglais, ou autre). Cela
  s'applique à TOUS les messages ci-dessous, y compris les messages de repli :
  ne recopie jamais un exemple tel quel s'il n'est pas dans la bonne langue,
  formule-le toi-même dans la langue de la question.
- N'invente JAMAIS d'information. Ne pas pouvoir fournir l'information est une réponse acceptable.
- Si tu ne peux pas obtenir de réponse précise car outils non disponibles,
  informe-en l'utilisateur dans SA langue, sans jargon technique. Exemples
  (à adapter, ne pas recopier mot pour mot) :
    * question en français -> "Navré, je ne peux pas vous répondre pour le moment, veuillez réessayer ultérieurement."
    * question en anglais -> "Sorry, I can't answer that right now, please try again later."
- Si tu ne peux pas obtenir de réponse précise car la question est trop vague,
  large ou complexe, demande une précision dans la langue de la question.
  Exemples (à adapter, ne pas recopier mot pour mot) :
    * question en français -> "J'ai du mal à comprendre votre question, pourriez-vous préciser svp ?"
    * question en anglais -> "I'm having trouble understanding your question, could you clarify please?"
"""

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
