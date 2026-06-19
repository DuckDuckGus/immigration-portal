import os
import sqlite3
import sys
from typing import Optional
import json
from mcp.server.fastmcp import FastMCP
from legal_logic import LegalBrain

# Initialize the MCP Server
mcp = FastMCP("Lex-Immigration-Portal-Server")

# --- ABSOLUTE PATH LOGIC ---
# Ensures the server finds the DB even when launched as a subprocess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

def _get_db_connection():
    """Verify database exists and connect."""
    if not os.path.exists(DB_PATH):
        # This will be visible in Lex's error logs
        raise FileNotFoundError(f"Database file missing at {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return results as dictionaries
    return conn

# ==========================================
# 1. SEARCH TOOLS
# ==========================================

@mcp.tool()
def search_clients(search_term: str, user_id: int) -> str:
    """Finds a client by name and includes spouse information if available."""
    fuzzy_term = f"%{search_term.strip()}%"
    
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Query now includes metadata to check for spouse info
    query = """
        SELECT c.client_id, c.full_name, c.nationality, c.metadata, e.name as case_type, cf.status
        FROM Clients c
        LEFT JOIN Case_Clients cc ON c.client_id = cc.client_id
        LEFT JOIN Case_Files cf ON cc.case_key = cf.case_key
        LEFT JOIN Engagement_Types e ON cf.eng_id = e.eng_id
        WHERE c.full_name LIKE ? OR c.nationality LIKE ?
    """
    params = [fuzzy_term, fuzzy_term]

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return f"SYSTEM MESSAGE: No client found matching '{search_term}'."
            
        results = [dict(row) for row in rows]

        # Post-process to find spouse information
        for res in results:
            client_meta = json.loads(res.get('metadata', '{}'))
            spouse_id = client_meta.get('spouse_id')
            
            if spouse_id:
                cursor.execute("SELECT full_name FROM Clients WHERE client_id = ?", (spouse_id,))
                spouse_row = cursor.fetchone()
                if spouse_row:
                    res['spouse_name'] = spouse_row['full_name']
            
            # Clean up internal data before returning to the LLM
            res.pop('metadata', None)
            res.pop('client_id', None)

        # Return as a JSON string for cleaner parsing by the LLM
        return json.dumps(results)

    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"
    finally:
        conn.close()

# ==========================================
# 2. AUDIT TOOLS
# ==========================================

@mcp.tool()
def audit_documents(user_id: int, limit: int = 15) -> str:
    """Identifies clients with missing documents (is_present = 0)."""
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Corrected JOIN: Case_Files does not have client_id. Join via Case_Clients.
    query = """
        SELECT c.full_name, dv.doc_type, e.name as case_type
        FROM Document_Vault dv
        JOIN Case_Files cf ON dv.case_key = cf.case_key
        JOIN Case_Clients cc ON cf.case_key = cc.case_key
        JOIN Clients c ON cc.client_id = c.client_id
        JOIN Engagement_Types e ON cf.eng_id = e.eng_id
        WHERE dv.is_present = 0
    """
    params = []

    query += f" LIMIT {limit}"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return "SYSTEM MESSAGE: All documents for your portfolio are accounted for."
            
        results = [dict(row) for row in rows]
        return str(results)
    finally:
        conn.close()

# ==========================================
# 3. CASE & TEAM DETAIL TOOLS
# ==========================================

@mcp.tool()
def get_case_details(case_key: str) -> str:
    """
    Retrieves full details for a single case file, including the assigned lawyer and document health.
    Use this to answer 'Who is in charge of X?' or 'Is case Y complete?'.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Fetch core case data and lawyer name
        cursor.execute("""
            SELECT cf.*, u.full_name as lawyer_name, et.name as engagement_name, et.required_docs,
                   (SELECT GROUP_CONCAT(cl.full_name, ', ') FROM Clients cl JOIN Case_Clients cc ON cl.client_id = cc.client_id WHERE cc.case_key = cf.case_key) as client_names
            FROM Case_Files cf
            LEFT JOIN Users u ON cf.lawyer_id = u.user_id
            JOIN Engagement_Types et ON cf.eng_id = et.eng_id
            WHERE cf.case_key LIKE ?
        """, (f"%{case_key}%",))
        
        case_row = cursor.fetchone()
        if not case_row:
            return f"SYSTEM MESSAGE: Case file '{case_key}' not found."
        
        case_data = dict(case_row)
        
        # Step 2: Fetch all documents for this case from the vault
        cursor.execute("SELECT * FROM Document_Vault WHERE case_key = ?", (case_key,))
        docs_metadata = [dict(r) for r in cursor.fetchall()]
        
        # Step 3: Use LegalBrain to calculate health metrics
        required_docs_list = json.loads(case_data['required_docs'])
        health_report = LegalBrain.get_case_health(case_data, docs_metadata, required_docs_list)
        
        # Step 4: Combine and return a clean summary
        summary = {
            "case_key": case_data['case_key'],
            "status": case_data['status'],
            "client_names": case_data['client_names'],
            "assigned_lawyer": case_data['lawyer_name'] or "Unassigned",
            "completeness_percent": health_report['completeness_score'],
            "urgency_score": health_report['urgency_score'],
            "flags": health_report['flags'],
            "is_ready_for_submission": health_report['ready_for_submission']
        }
        return json.dumps(summary)
        
    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_clients_for_lawyer(lawyer_name: str) -> str:
    """
    Finds all clients assigned to a specific lawyer. Use this to answer 'Who are [lawyer]'s clients?'.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    fuzzy_name = f"%{lawyer_name}%"
    
    try:
        query = """
            SELECT
                cl.full_name as client_name,
                cf.case_key,
                u.full_name as lawyer_name
            FROM Clients cl
            JOIN Case_Clients cc ON cl.client_id = cc.client_id
            JOIN Case_Files cf ON cc.case_key = cf.case_key
            JOIN Users u ON cf.lawyer_id = u.user_id
            WHERE u.full_name LIKE ?
            ORDER BY cf.case_key, cl.full_name;
        """
        cursor.execute(query, (fuzzy_name,))
        rows = cursor.fetchall()

        if not rows:
            return f"SYSTEM MESSAGE: No clients found for a lawyer named '{lawyer_name}'. Please check the name."

        results = [dict(row) for row in rows]
        return json.dumps(results)

    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def list_all_lawyers() -> str:
    """Returns a simple list of all lawyers in the firm."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM Users")
    rows = cursor.fetchall()
    conn.close()
    return str([row['full_name'] for row in rows])

# ==========================================
# 4. STATS TOOLS
# ==========================================

@mcp.tool()
def get_lawyer_stats() -> str:
    """Returns a breakdown of how many cases each lawyer is handling."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT u.full_name, COUNT(cf.case_key) as case_count
        FROM Users u
        JOIN Case_Files cf ON u.user_id = cf.lawyer_id
        GROUP BY u.full_name
        ORDER BY case_count DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    return str([dict(row) for row in rows])

if __name__ == "__main__":
    # Running via mcp.run() ensures the transport is STDIO by default
    mcp.run()