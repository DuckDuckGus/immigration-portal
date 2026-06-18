import sqlite3
import os
import json
from scripts.legal_logic import LegalBrain

class ImmigrationSDK:
    @staticmethod
    def _get_db():
        # Points to the database file created by database_setup.py
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.abspath(os.path.join(BASE_DIR, 'data', 'portal.db'))
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def fetch_cases(cls):
        conn = cls._get_db()
        cursor = conn.cursor()
        
        # Improved Query: Join Engagement/Lawyer and use a subquery for Client Names.
        cursor.execute("""
            SELECT c.*, e.name as engagement_name, e.required_docs, u.full_name as lawyer_name,
                   (SELECT GROUP_CONCAT(cl.full_name, ', ') FROM Clients cl 
                    JOIN Case_Clients cc ON cl.client_id = cc.client_id 
                    WHERE cc.case_key = c.case_key) as client_names
            FROM Case_Files c 
            JOIN Engagement_Types e ON c.eng_id = e.eng_id
            LEFT JOIN Users u ON c.lawyer_id = u.user_id
        """)
        
        results = []
        for row in cursor.fetchall():
            case = dict(row)
            
            # Parse required docs (JSON list) directly from Engagement_Types
            reqs = json.loads(case['required_docs'])
            
            # Fetch docs from Document_Vault by case_key
            cursor.execute("SELECT * FROM Document_Vault WHERE case_key = ?", (case['case_key'],))
            docs = [dict(r) for r in cursor.fetchall()]
            
            # Process health via LegalBrain
            health = LegalBrain.get_case_health(case, docs, reqs)
            
            # Enrich case dictionary with computed metrics
            case.update({
                "completeness": health["completeness_score"],
                "risk": health["risk_score"],
                "labels": health["labels"],
                "assigned_lawyer": case['lawyer_name'] or "Unassigned",
                "client_names": case['client_names'] or "Unknown Client"
            })
            results.append(case)
        conn.close()
        return results

    @classmethod
    def search_cases(cls, query_string="", sort_by="priority"):
        all_cases = cls.fetch_cases()
        parts = query_string.split()
        
        # Filtering logic
        active_labels = [p.split(":")[1] for p in parts if p.startswith("label:")]
        lawyer_filter = [p.split(":")[1] for p in parts if p.startswith("lawyer:")]
        free_text = [p for p in parts if ":" not in p]
        
        filtered = all_cases
        if active_labels:
            filtered = [c for c in filtered if any(l in c['labels'] for l in active_labels)]
        if lawyer_filter:
            filtered = [c for c in filtered if c['assigned_lawyer'] in lawyer_filter]
        if free_text:
            q = " ".join(free_text).lower()
            # Search by Case ID or Client Name
            filtered = [
                c for c in filtered 
                if q in c['case_key'].lower() or q in c['client_names'].lower()
            ]
            
        # Sorting logic
        if sort_by == "priority": filtered.sort(key=lambda x: x['risk'], reverse=True)
        elif sort_by == "completeness": filtered.sort(key=lambda x: x['completeness'], reverse=False)
        elif sort_by == "alpha": filtered.sort(key=lambda x: x['case_key'])
            
        return filtered

    @classmethod
    def fetch_lawyers(cls):
        conn = cls._get_db()
        cursor = conn.cursor()
        # Filters only users with 'Lawyer' role
        cursor.execute("SELECT user_id, full_name FROM Users WHERE role = 'Lawyer'")
        lawyers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return lawyers