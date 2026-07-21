# ai_service/main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from mcp import ClientSession
from mcp.client.sse import sse_client
import ollama
import uvicorn

# Initialisation de l'application FastAPI
app = FastAPI(
    title="AI Query Service",
    description="API REST permettant aux utilisateurs anonymes d'interroger l'inventaire en langage naturel.",
    version="1.0.0"
)

# Configuration CORS pour permettre au client Web (frontend) d'appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, restreindre aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des paramètres d'interconnexion
MODEL_NAME = "llama3.1"
MCP_SERVER_URL = "http://localhost:8000/sse"  # URL du serveur MCP Produit


# --- Modèles Pydantic (Validation des données) ---

class QueryRequest(BaseModel):
    question: str = Field(
        ..., 
        min_length=3, 
        example="Dans quelle succursale puis-je trouver le produit P100 ?",
        description="Question posée par l'utilisateur anonyme en langage naturel."
    )

class QueryResponse(BaseModel):
    question: str
    answer: str


# --- Logique de l'Agent IA ---

async def execute_agent_pipeline(user_prompt: str) -> str:
    """Consulte le serveur MCP via HTTP/SSE et génère la réponse via Ollama."""
    try:
        # 1. Connexion au serveur MCP distant via HTTP/SSE
        async with sse_client(MCP_SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Handshake MCP et récupération des outils disponibles
                await session.initialize()
                mcp_tools = await session.list_tools()

                # Conversion des outils au format reconnu par Ollama
                ollama_formatted_tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    }
                    for tool in mcp_tools.tools
                ]

                # Consigne système stricte pour éviter les hallucinations
                messages = [
                    {
                        "role": "system",
                        "content": (
                            """
                            Tu es un assistant virtuel d'inventaire pour notre entreprise de retail.
                            Ta tâche est de répondre aux questions des clients sur les produits et les stocks.

                            Consignes strictes :
                            1. Utilise TOUJOURS les outils MCP à ta disposition pour vérifier les détails des produits et les stocks.
                            2. N'invente JAMAIS d'informations (prix, stocks, caractéristiques).
                            3. Si les outils ne fournissent pas assez d'informations, réponds clairement que l'information n'est pas disponible.
                            4. Reste courtois, précis et concis.
                            """
                        )
                    },
                    {"role": "user", "content": user_prompt}
                ]

                # 2. Premier appel à Ollama avec les outils MCP injectés
                response = ollama.chat(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=ollama_formatted_tools
                )

                response_message = response['message']
                tool_calls = response_message.get('tool_calls')

                # 3. Si le LLM décide d'appeler un outil MCP
                if tool_calls:
                    messages.append(response_message)

                    for tool_call in tool_calls:
                        fn_name = tool_call['function']['name']
                        fn_args = tool_call['function']['arguments']

                        # Appel de l'outil à travers le réseau vers le serveur MCP
                        mcp_result = await session.call_tool(fn_name, fn_args)
                        tool_output = mcp_result.content[0].text

                        # Injection du résultat de l'outil dans le contexte
                        messages.append({
                            "role": "tool",
                            "content": tool_output
                        })

                    # 4. Deuxième appel à Ollama pour synthétiser la réponse finale
                    final_response = ollama.chat(
                        model=MODEL_NAME,
                        messages=messages
                    )
                    return final_response['message']['content']

                # Si aucun outil n'était nécessaire
                return response_message['content']

    except ConnectionRefusedError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de contacter le serveur MCP. Vérifiez qu'il est bien démarré sur le port 8000."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement de la requête IA : {str(e)}"
        )


# --- Endpoints REST ---

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Endpoint de contrôle d'état du service."""
    return {"status": "ok", "service": "ai_query_service"}


@app.post("/api/v1/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def ask_question(payload: QueryRequest):
    """Endpoint principal pour poser une question sur les produits et le stock."""
    answer = await execute_agent_pipeline(payload.question)
    return QueryResponse(question=payload.question, answer=answer)


if __name__ == "__main__":
    # Lancement du serveur Web FastAPI sur le port 8001
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)