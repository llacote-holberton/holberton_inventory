"""Module creating a server to expose End-user ('Client') interface"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path # To get current file's name without extension
import os
from dotenv import load_dotenv

# Loading environment vars
load_dotenv()
CLIENT_PORT = int(os.getenv("CLIENT_PORT", 8080))

app = FastAPI(title="Client Web Inventory")
module_name = Path(__file__).stem

# 1. API endpoints (note: must always be declared before "HTML routes")
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "client_web"}

# 2. Serves the whole "static_html" directory.
static_dir = os.path.join(os.path.dirname(__file__), "static_html")
app.mount(
    "/",
    # html=True makes Starlette ensure that request on '/' 
    #   automatically redirected to index.html inside dir.
    StaticFiles(directory=static_dir, html=True), 
    name="static"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(f"{module_name}:app", host="0.0.0.0", port=CLIENT_PORT, reload=True)
