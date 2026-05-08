from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import os
from scripts.legal_logic import LegalBrain

# 1. INITIALIZATION
app = FastAPI(title="Immigration Portal API")

# 2. SECURITY (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. DATABASE HELPER
def get_db_connection():
    # Construct path to be OS-independent
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "data", "portal.db")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

# 4. THE MAIN ENDPOINT
@app.get("/cases")
def list_cases():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # A. FETCH RAW INGREDIENTS
        cursor.execute("""
            SELECT cf.*, et.name as visa_name, et.required_docs 
            FROM Case_Files cf
            JOIN Engagement_Types et ON cf.eng_id = et.eng_id
        """)
        raw_cases = [dict(row) for row in cursor.fetchall()]

        processed_cases = []

        for case in raw_cases:
            # B. FETCH DOCUMENTS FOR THIS SPECIFIC CASE
            cursor.execute("SELECT * FROM Document_Vault WHERE case_key = ?", (case['case_key'],))
            docs = [dict(d) for d in cursor.fetchall()]

            # C. FETCH CLIENT METADATA
            cursor.execute("""
                SELECT c.metadata FROM Clients c
                JOIN Case_Clients cc ON c.client_id = cc.client_id
                WHERE cc.case_key = ? LIMIT 1
            """, (case['case_key'],))
            client_row = cursor.fetchone()
            client_meta = client_row['metadata'] if client_row else "{}"

            # D. THE HANDOFF: Pass ingredients to the Static Brain
            analysis = LegalBrain.get_case_flags(case, docs, client_meta)

            # E. COMBINE RAW DATA WITH BRAIN ANALYSIS
            case.update(analysis)
            processed_cases.append(case)

        return processed_cases

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# 5. START THE SERVER
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)