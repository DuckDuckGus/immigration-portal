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
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run the database_setup.py script first.")
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
            # Parse metadata string into an object for each document
            for doc in docs:
                try:
                    doc['metadata'] = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
                except (json.JSONDecodeError, TypeError):
                    doc['metadata'] = {} # Default to empty dict on error
            
            # Get a simple list of doc types that are present
            present_doc_types = [d['doc_type'] for d in docs if d.get('is_present')]
            
            # Process health via LegalBrain
            health = LegalBrain.get_case_health(case, docs, reqs)
            
            # Dynamically override status if the case is ready, addressing the user's observation.
            if health['ready_for_submission']:
                case['status'] = 'Ready for Submission'
            
            # Enrich case dictionary with computed metrics
            case.update({
                "completeness": health["completeness_score"],
                "urgency": health["urgency_score"],
                "labels": health["labels"],
                "assigned_lawyer": case['lawyer_name'] or "Unassigned",
                "lawyer_id": case['lawyer_id'],
                "client_names": case['client_names'] or "Unknown Client",
                "required_docs_list": reqs, # Pass the parsed list
                "present_docs_list": present_doc_types, # Pass the list of present docs
                "documents": docs # Pass the full document objects
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
        lawyer_filter = [p.split(":")[1].replace('_', ' ') for p in parts if p.startswith("lawyer:")]
        eng_filter = [p.split(":")[1].replace('_', ' ') for p in parts if p.startswith("eng:")]
        free_text = [p for p in parts if ":" not in p]
        
        filtered = all_cases
        if active_labels:
            filtered = [c for c in filtered if any(l in c['labels'] for l in active_labels)]
        if lawyer_filter:
            filtered = [c for c in filtered if c['assigned_lawyer'] in lawyer_filter]
        if eng_filter:
            filtered = [c for c in filtered if c['engagement_name'] in eng_filter]
        if free_text:
            q = " ".join(free_text).lower()
            # Search by Case ID or Client Name
            filtered = [
                c for c in filtered 
                if q in c['case_key'].lower() or q in c['client_names'].lower()
            ]
            
        # Sorting logic
        if sort_by == "priority": filtered.sort(key=lambda x: x['urgency'], reverse=True)
        elif sort_by == "completeness": filtered.sort(key=lambda x: x['completeness'], reverse=False)
        elif sort_by == "alpha": filtered.sort(key=lambda x: x['case_key'])
            
        return filtered

    @classmethod
    def fetch_lawyers(cls):
        conn = cls._get_db()
        cursor = conn.cursor()
        # Fetches all users since the 'role' concept has been removed
        cursor.execute("SELECT user_id, full_name FROM Users")
        lawyers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return lawyers

    @classmethod
    def fetch_engagement_types(cls):
        conn = cls._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM Engagement_Types ORDER BY name")
        eng_types = [row['name'] for row in cursor.fetchall()]
        conn.close()
        return eng_types

    @classmethod
    def fetch_client_details(cls, client_name: str):
        conn = cls._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Clients WHERE full_name = ?", (client_name,))
        client_data = cursor.fetchone()

        if not client_data:
            return None

        client_dict = dict(client_data)
        meta = json.loads(client_dict.get('metadata', '{}'))
        client_dict['metadata'] = meta # Replace JSON string with dict

        # If spouse exists, fetch their name
        spouse_id = meta.get('spouse_id')
        if spouse_id:
            cursor.execute("SELECT full_name FROM Clients WHERE client_id = ?", (spouse_id,))
            spouse_row = cursor.fetchone()
            if spouse_row:
                client_dict['spouse_name'] = spouse_row['full_name']

        conn.close()
        return client_dict

    @classmethod
    def fetch_lawyer_details(cls, lawyer_id: int):
        conn = cls._get_db()
        from collections import Counter
        cursor = conn.cursor()

        # 1. Get Lawyer's Name
        cursor.execute("SELECT full_name FROM Users WHERE user_id = ?", (lawyer_id,))
        lawyer_row = cursor.fetchone()
        if not lawyer_row:
            return {"error": "Lawyer not found"}

        # 2. Get all cases for this lawyer
        all_cases = cls.fetch_cases()
        lawyer_cases = [c for c in all_cases if c['lawyer_id'] == lawyer_id]

        # 3. Calculate Metrics
        total_cases = len(lawyer_cases)
        avg_urgency = round(sum(c['urgency'] for c in lawyer_cases) / total_cases, 1) if total_cases > 0 else 0
        avg_completeness = round(sum(c['completeness'] for c in lawyer_cases) / total_cases, 1) if total_cases > 0 else 0
        
        # 4. Engagement Breakdown for Chart
        engagement_counts = Counter(c['engagement_name'] for c in lawyer_cases)

        return {
            "full_name": lawyer_row['full_name'],
            "total_cases": total_cases,
            "avg_urgency": avg_urgency,
            "avg_completeness": avg_completeness,
            "cases": sorted(lawyer_cases, key=lambda x: x['urgency'], reverse=True), # Return cases sorted by urgency
            "engagement_breakdown": {
                "labels": list(engagement_counts.keys()),
                "data": list(engagement_counts.values())
            }
        }