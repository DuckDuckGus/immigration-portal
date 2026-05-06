import sqlite3
import os
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional

# Initialize the MCP Server
mcp = FastMCP("Lex Legal Portal Server")

# Ensure this points correctly to your database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

# ==========================================
# 1. PYDANTIC MODELS (Input Validation)
# ==========================================
class ClientSearchArgs(BaseModel):
    search_term: str = Field(..., description="The name of the client to search for.")
    user_id: int = Field(..., description="The ID of the lawyer making the request.")
    role: str = Field(..., description="'Admin' or 'Lawyer'")

class DocumentAuditArgs(BaseModel):
    user_id: int = Field(..., description="The ID of the lawyer making the request.")
    role: str = Field(..., description="'Admin' or 'Lawyer'")
    limit: int = Field(20, description="Max records to return to prevent token blowout.")

# ==========================================
# 2. INTERNAL LOGIC & SECURITY FIREWALL
# ==========================================
def _secure_query(query: str, params: tuple, user_id: int, role: str) -> list:
    """Handles DB connection and enforces row-level security."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if role != 'Admin':
        if "WHERE" in query.upper():
            query = query.replace("WHERE", "WHERE (") + f") AND (lawyer_id = {user_id})"
        else:
            query += f" WHERE lawyer_id = {user_id}"

    try:
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    except Exception as e:
        return [{"error": f"Database execution error: {str(e)}"}]
    finally:
        conn.close()

# ==========================================
# 3. EXPOSED MCP TOOLS
# ==========================================
@mcp.tool()
def search_clients(args: ClientSearchArgs) -> str:
    """
    Search for a client in the database. 
    Uses fuzzy matching to handle partial names.
    """
    # Intelligent Fuzzy Matching ("Luciano Canet" -> "%Luciano%Canet%")
    split_term = args.search_term.strip().replace(" ", "%")
    fuzzy_term = f"%{split_term}%"

    query = """
        SELECT c.full_name, c.nationality, cf.status
        FROM Clients c
        LEFT JOIN Case_Files cf ON c.client_id = cf.client_id
        WHERE c.full_name LIKE ?
        LIMIT 10
    """
    
    results = _secure_query(query, (fuzzy_term,), args.user_id, args.role)
    
    if not results:
        return (f"SYSTEM MESSAGE: No client found matching '{args.search_term}'. "
                f"Advise the user to try a partial name or check their spelling.")
    
    return str(results)

@mcp.tool()
def audit_documents(args: DocumentAuditArgs) -> str:
    """Returns missing documents, protected by pagination and security limits."""
    query = f"""
        SELECT c.full_name, dv.doc_type
        FROM Document_Vault dv
        JOIN Case_Files cf ON dv.case_key = cf.case_key
        JOIN Clients c ON cf.client_id = c.client_id
        WHERE dv.is_present = 0
        LIMIT {args.limit}
    """
    results = _secure_query(query, (), args.user_id, args.role)
    
    if not results:
        return "SYSTEM MESSAGE: All documents are up to date for this user's portfolio."
    
    if len(results) == args.limit:
        return str(results) + "\nSYSTEM MESSAGE: Limit reached. More missing docs exist."
        
    return str(results)

if __name__ == "__main__":
    # Runs the server on standard input/output
    mcp.run()