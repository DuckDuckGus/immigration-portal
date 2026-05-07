import sqlite3, os, json, random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('es_ES')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

def setup_final_comprehensive_db():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. DOCUMENT TYPES (The Metadata Blueprints)
    cursor.execute("CREATE TABLE Document_Types (type_id INTEGER PRIMARY KEY, name TEXT UNIQUE, required_keys TEXT)")
    doc_blueprints = [
        ("Passport", json.dumps(["expiry_date", "passport_number", "all_pages_scanned"])),
        ("Police Certificate", json.dumps(["issue_date", "has_apostille", "is_translated"])),
        ("Medical Certificate", json.dumps(["issue_date", "has_apostille"])),
        ("Official Medical Certificate", json.dumps(["issue_date", "has_apostille"])),
        ("Bank Statements", json.dumps(["balance_eur", "currency", "stamped_by_bank"])),
        ("Proof of Income", json.dumps(["balance_eur", "currency", "frequency"])),
        ("Health Insurance", json.dumps(["provider", "no_copay", "repatriation"])),
        ("Private Spanish Health Insurance", json.dumps(["provider", "no_copay", "repatriation"])),
        ("Work Contract", json.dumps(["salary_annual", "duration", "signed_by_company"])),
        ("Job Offer", json.dumps(["salary_annual", "signed_by_company"])),
        ("Business Plan", json.dumps(["viable_by_upt", "investment_amount"])),
        ("University Degree", json.dumps(["homologated", "level"])),
        ("Marriage/Partner Certificate", json.dumps(["issue_date", "has_apostille"])),
        ("Empadronamiento", json.dumps(["issue_date", "members_listed"])),
        ("Form 790-052", json.dumps(["issue_date", "paid_status"])),
        ("Company CIF", json.dumps(["cif_number", "is_active"])),
        ("Letter of Acceptance", json.dumps(["school_name", "start_date"])),
        ("Social Security Cert", json.dumps(["issue_date", "active_status"])),
        ("Work Experience Proof", json.dumps(["years_exp", "relevant_sector"])),
        ("Financial Feasibility", json.dumps(["projected_revenue", "capital_available"])),
        ("Professional Licenses", json.dumps(["license_number", "expiry_date"]))
    ]
    cursor.executemany("INSERT INTO Document_Types (name, required_keys) VALUES (?,?)", doc_blueprints)

    # 2. THE 8 ENGAGEMENT TYPES
    cursor.execute("CREATE TABLE Engagement_Types (eng_id INTEGER PRIMARY KEY, name TEXT, required_docs TEXT, base_price REAL)")
    eng_data = [
        (1, "Student Visa", json.dumps(["Passport", "Letter of Acceptance", "Bank Statements", "Health Insurance", "Police Certificate", "Medical Certificate"]), 800.0),
        (2, "Non-Lucrative Residency", json.dumps(["Passport", "Bank Statements", "Private Spanish Health Insurance", "Police Certificate", "Official Medical Certificate", "Form 790-052"]), 1500.0),
        (3, "EU Family Members", json.dumps(["Passport", "Marriage/Partner Certificate", "Bank Statements", "Empadronamiento"]), 1200.0),
        (4, "Work Permit (Employee)", json.dumps(["Passport", "Job Offer", "Company CIF", "Police Certificate", "Medical Certificate"]), 2000.0),
        (5, "Highly Skilled Professional", json.dumps(["Passport", "University Degree", "Work Contract", "Company CIF"]), 2500.0),
        (6, "EU Blue Card", json.dumps(["Passport", "University Degree", "Work Contract", "Work Experience Proof"]), 2800.0),
        (7, "Digital Nomad", json.dumps(["Passport", "Work Contract", "Proof of Income", "Social Security Cert", "Police Certificate"]), 1800.0),
        (8, "Work Permit (Self-Employed)", json.dumps(["Passport", "Business Plan", "Financial Feasibility", "Professional Licenses", "Police Certificate"]), 2200.0)
    ]
    cursor.executemany("INSERT INTO Engagement_Types VALUES (?,?,?,?)", eng_data)

    # 3. CORE TABLES
    cursor.execute("CREATE TABLE Users (user_id INTEGER PRIMARY KEY, full_name TEXT, role TEXT)")
    cursor.execute("""CREATE TABLE Clients (
        client_id INTEGER PRIMARY KEY, 
        full_name TEXT, 
        nationality TEXT, 
        email TEXT,
        metadata TEXT 
    )""")
    cursor.execute("CREATE TABLE Case_Files (case_key TEXT PRIMARY KEY, lawyer_id INTEGER, eng_id INTEGER, status TEXT, adjustment_rate REAL, total_fee REAL)")
    cursor.execute("CREATE TABLE Case_Clients (case_key TEXT, client_id INTEGER)")
    cursor.execute("CREATE TABLE Document_Vault (doc_id INTEGER PRIMARY KEY, case_key TEXT, client_id INTEGER, doc_type TEXT, is_present BOOLEAN, metadata TEXT, updated_at DATETIME)")

    # 4. TEAM: 5 LAWYERS + 1 ADMIN
    users = [(1, "Elena Ruiz", "Lawyer"), (2, "Iñigo Larrea", "Lawyer"), (3, "Javi Montoya", "Lawyer"), 
             (4, "Bea Iglesia", "Lawyer"), (5, "Mateo Vizcaíno", "Lawyer"), (6, "Lucía Méndez", "Admin")]
    cursor.executemany("INSERT INTO Users VALUES (?,?,?)", users)

    # 5. SEED 50 CASES
    nats = ["USA", "UK", "Canada", "Philippines", "Mexico", "Brazil"]
    for i in range(1, 51):
        eng = random.choice(eng_data)
        adj_rate = round(random.uniform(0.9, 1.4), 2)
        last_name = fake.last_name().upper().replace(" ", "_")
        case_key = f"{last_name}_2026_{100+i}"
        
        cursor.execute("INSERT INTO Case_Files VALUES (?,?,?,?,?,?)", 
                       (case_key, random.randint(1, 5), eng[0], "In Progress", adj_rate, round(eng[3] * adj_rate, 2)))

        # Handle Marriage/Multi-Client logic
        is_married = random.random() < 0.20
        case_participants = []
        
        if is_married:
            p_id = cursor.execute("INSERT INTO Clients (full_name, nationality, email, metadata) VALUES (?,?,?,?)",
                                 (f"{fake.first_name()} {fake.last_name()}", random.choice(nats), fake.email(), json.dumps({"is_married": True}))).lastrowid
            s_id = cursor.execute("INSERT INTO Clients (full_name, nationality, email, metadata) VALUES (?,?,?,?)",
                                 (f"{fake.first_name()} {fake.last_name()}", random.choice(nats), fake.email(), json.dumps({"is_married": True, "spouse_id": p_id}))).lastrowid
            cursor.execute("UPDATE Clients SET metadata = ? WHERE client_id = ?", (json.dumps({"is_married": True, "spouse_id": s_id}), p_id))
            case_participants = [p_id, s_id]
        else:
            p_id = cursor.execute("INSERT INTO Clients (full_name, nationality, email, metadata) VALUES (?,?,?,?)",
                                 (f"{fake.first_name()} {fake.last_name()}", random.choice(nats), fake.email(), json.dumps({"is_married": False}))).lastrowid
            case_participants = [p_id]

        for c_id in case_participants:
            cursor.execute("INSERT INTO Case_Clients (case_key, client_id) VALUES (?,?)", (case_key, c_id))
            for doc_name in json.loads(eng[2]):
                is_present = random.choice([0, 1])
                cursor.execute("SELECT required_keys FROM Document_Types WHERE name = ?", (doc_name,))
                req_keys = json.loads(cursor.fetchone()[0])
                meta = {key: (fake.bothify("??###") if is_present else None) for key in req_keys}
                cursor.execute("INSERT INTO Document_Vault (case_key, client_id, doc_type, is_present, metadata, updated_at) VALUES (?,?,?,?,?,?)",
                               (case_key, c_id, doc_name, is_present, json.dumps(meta), datetime.now().isoformat()))

    conn.commit()
    conn.close()
    print("DB Created")

if __name__ == "__main__":
    setup_final_comprehensive_db()