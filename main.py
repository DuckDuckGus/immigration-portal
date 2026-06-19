import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sdk import ImmigrationSDK
from scripts.lex_engine import LexEngine

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Mount the static directory so CSS and JS can be loaded by the browser
static_path = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# 2. Update the path to point into your sub-folder
@app.get("/")
async def serve_dashboard():
    # Use absolute path to ensure the file is found regardless of where uvicorn is started
    return FileResponse(os.path.join(static_path, "templates", "index.html"))

@app.get("/api/get_cases")
def get_cases(q: str = "", sort: str = "priority"):
    return ImmigrationSDK.search_cases(query_string=q, sort_by=sort)

@app.get("/api/get_lawyers")
def get_lawyers():
    return ImmigrationSDK.fetch_lawyers()

@app.get("/api/get_engagement_types")
def get_engagement_types():
    return ImmigrationSDK.fetch_engagement_types()

@app.get("/api/get_client_details/{client_name}")
def get_client_details(client_name: str):
    details = ImmigrationSDK.fetch_client_details(client_name.replace('_', ' '))
    if not details:
        return {"error": "Client not found"}
    return details

@app.get("/api/get_lawyer_details/{lawyer_id}")
def get_lawyer_details(lawyer_id: int):
    details = ImmigrationSDK.fetch_lawyer_details(lawyer_id)
    if "error" in details:
        return details, 404
    return details

class LexQuery(BaseModel):
    prompt: str
    user_id: int = 1 # Defaulting to user 1 for now

@app.post("/api/ask_lex")
async def ask_lex(query: LexQuery):
    # This instantiates the engine for each request.
    # For a production app, you might manage this differently (e.g., singleton).
    lex = LexEngine(user_id=query.user_id)
    answer = await lex.ask_mcp(query.prompt)
    return {"answer": answer}
