import json
from datetime import datetime

class LegalBrain:
    # IPREM/SMI Thresholds for 2026 (Simulated)
    THRESHOLDS = {
        "Digital Nomad": 32000,
        "Non-Lucrative Residency": 29000,
        "Student Visa": 7200
    }

    @staticmethod
    def get_case_flags(case_data, docs_metadata, client_metadata):
        """
        Input: 
        - case_data: dict from Case_Files table
        - docs_metadata: list of dicts from Document_Vault
        - client_metadata: dict from Clients.metadata
        """
        flags = []
        valid_docs_count = 0
        total_required = len(docs_metadata)

        # 1. Financial Flags
        if case_data.get('total_fee', 0) > 0 and case_data.get('status') == 'Unpaid':
            flags.append("NOT_PAID")
        
        if case_data.get('adjustment_rate', 1.0) < 1.0:
            flags.append("DISCOUNT_APPLIED")
        elif case_data.get('adjustment_rate', 1.0) > 1.0:
            flags.append("SURCHARGE_APPLIED")

        # 2. Relationship Flags
        client_meta = json.loads(client_metadata) if isinstance(client_metadata, str) else client_metadata
        if client_meta.get("is_married") and not any(d['doc_type'] == 'Marriage/Partner Certificate' and d['is_present'] for d in docs_metadata):
            flags.append("MISSING_SPOUSE_DATA")

        # 3. Document-Level Validation Logic
        for doc in docs_metadata:
            is_valid = True
            doc_meta = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
            
            if not doc['is_present']:
                is_valid = False
            else:
                # Expiry Check
                if "expiry_date" in doc_meta and doc_meta["expiry_date"]:
                    expiry = datetime.strptime(doc_meta["expiry_date"], "%Y-%m-%d")
                    if (expiry - datetime.now()).days < 180:
                        flags.append(f"EXPIRY_RISK_{doc['doc_type'].upper()}")
                        if (expiry - datetime.now()).days < 0: is_valid = False

                # Legalization Check
                if "has_apostille" in doc_meta and doc_meta["has_apostille"] is False:
                    flags.append(f"LEGALIZATION_GAP_{doc['doc_type'].upper()}")
                    is_valid = False

                # Freshness (Stale) Check
                if "issue_date" in doc_meta and doc_meta["issue_date"]:
                    issue = datetime.strptime(doc_meta["issue_date"], "%Y-%m-%d")
                    if (datetime.now() - issue).days > 90:
                        flags.append(f"STALE_DOC_{doc['doc_type'].upper()}")
                        is_valid = False

                # Translation Check
                if "is_translated" in doc_meta and doc_meta["is_translated"] is False:
                    flags.append(f"TRANSLATION_REQ_{doc['doc_type'].upper()}")
                    is_valid = False

            if is_valid:
                valid_docs_count += 1

        # 4. Final Completion Logic
        completion_rate = round((valid_docs_count / total_required) * 100, 1) if total_required > 0 else 0
        
        if completion_rate < 100:
            flags.append("INCOMPLETE_VAULT")

        return {
            "completion_rate": completion_rate,
            "flags": list(set(flags)), # Deduplicate flags
            "ready_for_submission": completion_rate == 100 and "NOT_PAID" not in flags
        }