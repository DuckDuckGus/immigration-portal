from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from scripts.legal_logic import LegalBrain

app = FastAPI(title="Immigration Portal SDK")

# 1. SECURITY: Open the door for your JavaScript UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your GitHub Pages URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ROBUST PATHING: Find the DB no matter where the app is running
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "portal.db")

def get_db():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 3. THE "ALL CASES" ENDPOINT (The heart of your dashboard)
@app.get("/api/v1/cases")
def get_dashboard_data():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Join Case_Files with Engagement_Types to get the "Rules" for each case
        cursor.execute("""
            SELECT cf.*, et.name as visa_name, et.required_docs 
            FROM Case_Files cf
            JOIN Engagement_Types et ON cf.eng_id = et.eng_id
        """)
        cases = [dict(row) for row in cursor.fetchall()]

        results = []
        for case in cases:
            # Fetch Docs for this case
            cursor.execute("SELECT * FROM Document_Vault WHERE case_key = ?", (case['case_key'],))
            docs = [dict(d) for d in cursor.fetchall()]

            # Fetch Client Meta (for marriage/profile flags)
            cursor.execute("""
                SELECT c.metadata FROM Clients c
                JOIN Case_Clients cc ON c.client_id = cc.client_id
                WHERE cc.case_key = ? LIMIT 1
            """, (case['case_key'],))
            client_row = cursor.fetchone()
            client_meta = client_row['metadata'] if client_row else "{}"

            # PROCESS logic via the Static Brain
            analysis = LegalBrain.get_case_flags(case, docs, client_meta)
            
            # Merge and clean up
            case.update(analysis)
            results.append(case)

        conn.close()
        return results

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 4. SINGLE CASE ENDPOINT (For when a lawyer clicks a specific row)
@app.get("/api/v1/cases/{case_key}")
def get_case_detail(case_key: str):
    # This will return the granular list of every document and its specific flags
    # Useful for the "Deep Dive" view in your JS UI
    pass

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)