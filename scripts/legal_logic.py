import json
from datetime import datetime

class LegalBrain:
    """
    The LegalBrain processes case health based on dynamic requirements.
    It no longer contains hardcoded visa rules, allowing the database 
    to act as the single source of truth.
    """

    DEFAULT_FLAG_WEIGHTS = {
        "EXPIRED_DOC": 10,
        "MISSING_APOSTILLE": 10,
        "INVALID_DATE_FORMAT": 8,
        "STALE_DOC": 5,
        "EXPIRY_URGENCY": 5,
        "TRANSLATION_REQ": 3,
        "INCOMPLETE_VAULT": 5
    }

    @staticmethod
    def get_case_health(case_data, docs_metadata, required_docs_list):
        """
        Calculates triage metrics.
        :param case_data: Dict of case info
        :param docs_metadata: List of dicts representing present documents
        :param required_docs_list: List of strings (e.g., ["PASSPORT", "OFFER_LETTER"])
                                   Fetched dynamically from DB before calling this.
        """
        flags = []
        total_required = len(required_docs_list)
        
        # A. Calculate Completeness
        # Check which required doc types are present and marked as valid
        present_types = [d['doc_type'] for d in docs_metadata if d.get('is_present')]
        valid_docs_count = sum(1 for req in required_docs_list if req in present_types)
        
        if valid_docs_count < total_required:
            flags.append("INCOMPLETE_VAULT")
            
        completeness_rate = round((valid_docs_count / total_required) * 100, 1) if total_required > 0 else 0

        # B. Calculate Urgency Score
        urgency_score = 0
        
        # Audit logic for existing docs
        for doc in docs_metadata:
            if not doc.get('is_present'): continue
            
            # Metadata is expected as a dict or parsed JSON string
            doc_meta = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
            
            # Expiry Check
            if doc_meta.get("expiry_date"):
                try:
                    expiry = datetime.strptime(doc_meta["expiry_date"], "%Y-%m-%d")
                    days_left = (expiry - datetime.now()).days
                    if days_left < 0: flags.append("EXPIRED_DOC")
                    elif days_left < 180: flags.append("EXPIRY_URGENCY")
                except (ValueError, TypeError): 
                    flags.append("INVALID_DATE_FORMAT")
            
            # Apostille & Translation Check
            if doc_meta.get("has_apostille") == False: # Explicitly check for False
                flags.append("MISSING_APOSTILLE")
            
            if doc_meta.get("is_translated") == False: # Explicitly check for False
                flags.append("TRANSLATION_REQ")


        # Sum weighted risks
        unique_flags = list(set(flags))
        for flag in unique_flags:
            urgency_score += LegalBrain.DEFAULT_FLAG_WEIGHTS.get(flag, 1)

        # Completeness Penalty: Heavier weight for significantly incomplete files
        if completeness_rate < 50: urgency_score += 20
        elif completeness_rate < 90: urgency_score += 10
        
        urgency_score = min(urgency_score, 100)

        return {
            "completeness_score": completeness_rate,
            "urgency_score": urgency_score,
            "flags": unique_flags,
            "lawyer": case_data.get('lawyer_name', 'Unassigned'),
            "labels": LegalBrain._generate_labels(completeness_rate, urgency_score),
            "ready_for_submission": completeness_rate == 100 and urgency_score < 10
        }

    @staticmethod
    def _generate_labels(completeness, risk):
        labels = []
        if risk > 50: labels.append("HIGH_URGENCY")
        if completeness < 80: labels.append("GATHERING")
        if risk < 20 and completeness == 100: labels.append("READY_TO_FILE") # Renaming HIGH_RISK to HIGH_URGENCY will be done in CSS/JS
        return labels