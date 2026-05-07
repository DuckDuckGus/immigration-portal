import os
import sqlite3
import sys
from typing import Optional
from mcp.server.fastmcp import FastMCP

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
def search_clients(search_term: str, user_id: int, role: str) -> str:
    """
    Finds a client by name. 
    Use 'Admin' role to see all, 'Lawyer' to see assigned cases.
    """
    # Create a fuzzy pattern: "Mali" -> "%Mali%"
    fuzzy_term = f"%{search_term.strip()}%"
    
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Base Query
    query = """
        SELECT c.full_name, c.nationality, cf.case_type, cf.status
        FROM Clients c
        LEFT JOIN Case_Files cf ON c.client_id = cf.client_id
        WHERE c.full_name LIKE ?
    """
    params = [fuzzy_term]

    # Security Firewall: If not Admin, filter by lawyer_id
    if role != 'Admin':
        query += " AND cf.lawyer_id = ?"
        params.append(user_id)

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return f"SYSTEM MESSAGE: No client found matching '{search_term}'."
            
        # Convert sqlite3.Row objects to readable string for Lex
        results = [dict(row) for row in rows]
        return str(results)
    except Exception as e:
        return f"DATABASE ERROR: {str(e)}"
    finally:
        conn.close()

# ==========================================
# 2. AUDIT TOOLS
# ==========================================

@mcp.tool()
def audit_documents(user_id: int, role: str, limit: int = 15) -> str:
    """
    Identifies clients with missing documents (is_present = 0).
    Best used for proactive management of immigration files.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.full_name, dv.doc_type, cf.case_type
        FROM Document_Vault dv
        JOIN Case_Files cf ON dv.case_key = cf.case_key
        JOIN Clients c ON cf.client_id = c.client_id
        WHERE dv.is_present = 0
    """
    params = []

    # Security Firewall
    if role != 'Admin':
        query += " AND cf.lawyer_id = ?"
        params.append(user_id)

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
# 3. STATS TOOLS (New!)
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