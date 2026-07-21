# ai_query_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp import ClientSession
from mcp.client.sse import sse_client
import ollama

app = FastAPI(title="AI Query Service")

# Configuration des accès
MODEL_NAME = "llama3.1"
MCP_SERVER_URL = "http://localhost:8000/sse"

# Modèle de requête entrante
class QueryRequest(BaseModel):
    question: str

async def process_agent_query(user_prompt: str) -> str:
    """Consulte le serveur MCP via HTTP et interroge le LLM."""
    try:
        # 1. Connexion HTTP/SSE au serveur MCP
        async with sse_client(MCP_SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                
                # 2. Handshake MCP & Découverte des outils
                await session.initialize()
                mcp_tools = await session.list_tools()

                # 3. Formatage des outils pour Ollama
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

                messages = [{"role": "user", "content": user_prompt}]

                # 4. Premier appel à Ollama avec les outils MCP
                response = ollama.chat(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=ollama_formatted_tools
                )

                response_message = response['message']
                tool_calls = response_message.get('tool_calls')

                # 5. Exécution de l'outil MCP si demandé par le LLM
                if tool_calls:
                    messages.append(response_message)

                    for tool_call in tool_calls:
                        fn_name = tool_call['function']['name']
                        fn_args = tool_call['function']['arguments']

                        print(f"🌐 [Agent] Execution outil MCP via HTTP : {fn_name}({fn_args})")

                        # Appel distant au serveur MCP
                        mcp_result = await session.call_tool(fn_name, fn_args)
                        tool_output = mcp_result.content[0].text

                        # Injection du résultat dans la conversation
                        messages.append({
                            "role": "tool",
                            "content": tool_output
                        })

                    # 6. Synthèse finale de la réponse par le LLM
                    final_response = ollama.chat(
                        model=MODEL_NAME,
                        messages=messages
                    )
                    return final_response['message']['content']

                return response_message['content']

    except Exception as e:
        print(f"❌ Erreur lors du traitement : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur du service IA: {str(e)}")

# Point d'entrée REST pour l'interface client Web
@app.post("/query")
async def handle_query(payload: QueryRequest):
    answer = await process_agent_query(payload.question)
    return {"question": payload.question, "answer": answer}

if __name__ == "__main__":
    import uvicorn
    # Lancement du service IA sur le port 8001
    uvicorn.run(app, host="0.0.0.0", port=8002)