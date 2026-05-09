import sqlite3
import os
from scripts.legal_logic import LegalBrain

class ImmigrationSDK:
    """The Engine for the Immigration Portal"""
    
    @staticmethod
    def _get_db():
        # Using relative paths to work both on Mac and Streamlit Cloud
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "data", "portal.db")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def fetch_cases(cls):
        """Fetches all 50 cases with automated legal flags"""
        conn = cls._get_db()
        cursor = conn.cursor()
        
        # Joined query for Cases + Visa Types
        cursor.execute("""
            SELECT cf.*, et.name as visa_name, et.required_docs 
            FROM Case_Files cf
            JOIN Engagement_Types et ON cf.eng_id = et.eng_id
        """)
        
        results = []
        for row in cursor.fetchall():
            case = dict(row)
            
            # Fetch metadata to check Spanish naming and document rules
            cursor.execute("""
                SELECT metadata FROM Clients 
                WHERE client_id IN (SELECT client_id FROM Case_Clients WHERE case_key=?)
            """, (case['case_key'],))
            
            client_row = cursor.fetchone()
            meta = client_row['metadata'] if client_row else "{}"
            
            # Run the Legal-Tech logic for flags (Stale docs, missing phone, etc.)
            analysis = LegalBrain.get_case_flags(case, [], meta)
            case.update(analysis)
            results.append(case)
            
        conn.close()
        return results