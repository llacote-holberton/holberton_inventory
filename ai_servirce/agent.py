import os
from anthropic import Anthropic
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://product_mcp_server:8001/mcp")
MODEL = "claude-sonnet-4-6"

anthropic_client = Anthropic()  # lit ANTHROPIC_API_KEY dans l'environnement

SYSTEM_PROMPT = (
    "Tu es un assistant qui répond à des questions sur des produits et du "
    "stock en te basant UNIQUEMENT sur les informations renvoyées par les "
    "outils disponibles. Si les outils ne fournissent pas assez "
    "d'informations pour répondre avec certitude, dis explicitement que "
    "l'information n'est pas disponible. N'invente jamais de données "
    "(prix, quantités, noms de produits, etc.)."
)


def _mcp_tools_to_anthropic_format(mcp_tools) -> list[dict]:
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema,
        }
        for t in mcp_tools
    ]


async def answer_question(question: str) -> str:
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tools = _mcp_tools_to_anthropic_format(tools_result.tools)

            messages = [{"role": "user", "content": question}]

            # Sécurité : on limite le nombre d'aller-retours pour éviter
            # une boucle infinie si le modèle s'entête à appeler des tools.
            for _ in range(6):
                response = anthropic_client.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason != "tool_use":
                    return "".join(
                        block.text for block in response.content if block.type == "text"
                    )

                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = await session.call_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": [c.model_dump() for c in result.content],
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

            return "Je n'ai pas réussi à obtenir une réponse fiable, réessaie ta question."


async def answer_question_stream(question: str):
    """
    Même boucle que answer_question, mais chaque étape utilise
    `messages.stream(...)` au lieu de `messages.create(...)` : on obtient
    les morceaux de texte au fur et à mesure qu'ils sont générés, au lieu
    d'attendre la réponse complète.

    Important : on garde UN SEUL appel réseau par étape (pas
    stream() PUIS create() en double) : `stream.get_final_message()`
    donne le message complet une fois le flux terminé, ce qui suffit pour
    savoir si Claude demande un tool et pour construire l'historique.
    """
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tools = _mcp_tools_to_anthropic_format(tools_result.tools)

            messages = [{"role": "user", "content": question}]

            for _ in range(6):
                with anthropic_client.messages.stream(
                    model=MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=tools,
                    messages=messages,
                ) as stream:
                    for text_chunk in stream.text_stream:
                        yield text_chunk
                    final_message = stream.get_final_message()

                if final_message.stop_reason != "tool_use":
                    return

                messages.append({"role": "assistant", "content": final_message.content})

                tool_results = []
                for block in final_message.content:
                    if block.type != "tool_use":
                        continue
                    result = await session.call_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": [c.model_dump() for c in result.content],
                        }
                    )

                messages.append({"role": "user", "content": tool_results})

    yield "\n[Je n'ai pas réussi à obtenir une réponse fiable, réessaie ta question.]"
