import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sdk import ImmigrationSDK

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
