import sqlite3, os, json, random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('es_ES')
fake_international = Faker() # For non-Spanish addresses
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

def _generate_realistic_value(key, fake_instance):
    """Smart factory to generate realistic data based on the required key name."""
    
    # 1. DATES (YYYY-MM-DD)
    if "date" in key:
        if key == "issue_date":
            # Sometime in the past 3 years
            return fake_instance.date_between(start_date='-3y', end_date='today').strftime("%Y-%m-%d")
        elif key == "expiry_date":
            # Past 1 year (risky) or next 5 years (valid)
            return fake_instance.date_between(start_date='-1y', end_date='+5y').strftime("%Y-%m-%d")
        elif key == "start_date":
            return fake_instance.date_between(start_date='today', end_date='+1y').strftime("%Y-%m-%d")
    
    # 2. BOOLEANS (Legal validations)
    elif key.startswith("is_") or key.startswith("has_") or key in ["all_pages_scanned", "stamped_by_bank", "no_copay", "repatriation", "signed_by_company", "viable_by_upt", "homologated", "active_status"]:
        # 80% chance of being True to simulate mostly valid docs, with some risky ones
        return random.random() < 0.80
    
    # 3. FINANCIALS
    elif key in ["balance_eur", "salary_annual", "investment_amount", "projected_revenue", "capital_available"]:
        return round(random.uniform(5000, 80000), 2)
    elif key == "currency":
        return random.choices(["EUR", "USD", "GBP"], weights=[0.85, 0.1, 0.05])[0]
    
    # 4. SPECIFIC STRINGS & NUMBERS
    elif key == "school_name":
        return f"Universidad de {fake_instance.city()}"
    elif key == "passport_number":
        return fake_instance.bothify(text='??#######', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    elif key == "provider":
        return random.choice(["Sanitas", "Adeslas", "DKV", "Asisa", "Mapfre"])
    elif key == "frequency":
        return random.choice(["Monthly", "Annually"])
    elif key == "duration":
        return random.choice(["1 year", "Indefinite", "6 months"])
    elif key == "level":
        return random.choice(["Bachelor", "Master", "PhD"])
    elif key == "paid_status":
        return random.choice(["Paid", "Unpaid"])
    elif key == "cif_number":
        return fake_instance.bothify(text='B########')
    elif key == "years_exp":
        return random.randint(1, 15)
    elif key == "relevant_sector":
        return fake_instance.job()
    elif key == "members_listed":
        return random.randint(1, 5)
    elif key == "license_number":
        return fake_instance.bothify(text='LIC-#####')
    
    # Fallback for anything missed
    return fake_instance.word()

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
        ("Company CIF", json.dumps(["cif_number", "active_status"])),
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
    cursor.execute("CREATE TABLE Users (user_id INTEGER PRIMARY KEY, full_name TEXT)")
    cursor.execute("""CREATE TABLE Clients (
        client_id INTEGER PRIMARY KEY, 
        full_name TEXT, 
        nationality TEXT,
        dob TEXT,
        street_address TEXT,
        city TEXT,
        postal_code TEXT,
        country TEXT,
        email TEXT,
        metadata TEXT 
    )""")
    cursor.execute("CREATE TABLE Case_Files (case_key TEXT PRIMARY KEY, lawyer_id INTEGER, eng_id INTEGER, status TEXT, adjustment_rate REAL, total_fee REAL)")
    cursor.execute("CREATE TABLE Case_Clients (case_key TEXT, client_id INTEGER)")
    cursor.execute("CREATE TABLE Document_Vault (doc_id INTEGER PRIMARY KEY, case_key TEXT, client_id INTEGER, doc_type TEXT, is_present BOOLEAN, metadata TEXT, updated_at DATE)")

    # 4. TEAM: 5 LAWYERS + 1 ADMIN
    users = [(1, "Elena Ruiz"), (2, "Iñigo Larrea"), (3, "Javi Montoya"), 
             (4, "Bea Iglesia"), (5, "Mateo Vizcaíno"), (6, "Lucía Méndez")]
    cursor.executemany("INSERT INTO Users VALUES (?,?)", users)

    # 5. SEED 50 CASES
    nats = ["USA", "UK", "Canada", "Philippines", "Mexico", "Brazil", "Argentina", "Venezuela", "Colombia", "Peru", "Chile", "Ecuador", "Bolivia"]
    for i in range(1, 201):
        eng = random.choice(eng_data)
        adj_rate = round(random.uniform(0.9, 1.4), 2)
        
        # Generate primary client details first to ensure names match the case key
        p_first = fake.first_name()
        p_last = fake.last_name()
        case_key = f"{p_last.upper().replace(' ', '_')}_2026_{100+i}"

        cursor.execute("INSERT INTO Case_Files VALUES (?,?,?,?,?,?)", 
                       (case_key, random.randint(1, 6), eng[0], "In Progress", adj_rate, round(eng[3] * adj_rate, 2)))

        # Handle Marriage/Multi-Client logic
        is_married = random.random() < 0.20
        case_participants = []
        
        # Base client data - create international addresses for the first 43 clients
        if i <= 43:
            address_country = fake_international.country()
            # Ensure the generated country is not Spain for this cohort
            while address_country == "Spain":
                address_country = fake_international.country()
            
            street = fake_international.street_address()
            city = fake_international.city()
            postal_code = fake_international.postcode()
        else:
            address_country, street, city, postal_code = "Spain", fake.street_address(), fake.city(), fake.postcode()

        client_base_data = (
            random.choice(nats),
            fake.date_of_birth(minimum_age=20, maximum_age=65).strftime("%Y-%m-%d"),
            street, city, postal_code, address_country,
            fake.email()
        )

        if is_married:
            dom = fake.date_between(start_date='-10y', end_date='today').strftime("%Y-%m-%d")
            p_meta = {"is_married": True, "date_of_marriage": dom}
            s_meta = {"is_married": True, "date_of_marriage": dom}
            p_id = cursor.execute("INSERT INTO Clients (full_name, nationality, dob, street_address, city, postal_code, country, email, metadata) VALUES (?,?,?,?,?,?,?,?,?)", (f"{p_first} {p_last}", *client_base_data, json.dumps(p_meta))).lastrowid
            s_id = cursor.execute("INSERT INTO Clients (full_name, nationality, dob, street_address, city, postal_code, country, email, metadata) VALUES (?,?,?,?,?,?,?,?,?)", (f"{fake.first_name()} {p_last}", *client_base_data, json.dumps(s_meta))).lastrowid
            # Update each other's metadata with spouse_id
            cursor.execute("UPDATE Clients SET metadata = json_set(metadata, '$.spouse_id', ?) WHERE client_id = ?", (s_id, p_id))
            cursor.execute("UPDATE Clients SET metadata = json_set(metadata, '$.spouse_id', ?) WHERE client_id = ?", (p_id, s_id))
            case_participants = [p_id, s_id]
        else:
            p_id = cursor.execute("INSERT INTO Clients (full_name, nationality, dob, street_address, city, postal_code, country, email, metadata) VALUES (?,?,?,?,?,?,?,?,?)", (f"{p_first} {p_last}", *client_base_data, json.dumps({"is_married": False}))).lastrowid
            case_participants = [p_id]

        for c_id in case_participants:
            cursor.execute("INSERT INTO Case_Clients (case_key, client_id) VALUES (?,?)", (case_key, c_id))
            for doc_name in json.loads(eng[2]):
                # --- Logic to create high-urgency cases ---
                # For the first 15 cases, ensure at least one doc is missing
                if i <= 15 and "Bank Statements" in doc_name:
                    is_present = 0
                else:
                    is_present = random.choice([0, 1])
                
                # Fetch exact required keys for this specific doc_type
                cursor.execute("SELECT required_keys FROM Document_Types WHERE name = ?", (doc_name,))
                req_keys = json.loads(cursor.fetchone()[0])
                
                # Generate realistic metadata using the helper function
                meta = {}
                if i <= 15 and "Police Certificate" in doc_name:
                    meta = {"issue_date": fake.date_between(start_date='-2y', end_date='-1y').strftime("%Y-%m-%d"), "has_apostille": False, "is_translated": False}
                    is_present = 1 # Make sure the bad doc is present
                elif i <= 15 and "Passport" in doc_name:
                    meta = {"expiry_date": fake.date_between(start_date='-1y', end_date='-1d').strftime("%Y-%m-%d"), "passport_number": fake.bothify(text='??#######'), "all_pages_scanned": True}
                    is_present = 1 # Make sure the expired doc is present
                elif is_present:
                    for key in req_keys:
                        meta[key] = _generate_realistic_value(key, fake)
                
                # If doc is not present, metadata should be empty
                if not is_present:
                    meta = {key: None for key in req_keys}
                
                # Insert with Date only (no time)
                cursor.execute("INSERT INTO Document_Vault (case_key, client_id, doc_type, is_present, metadata, updated_at) VALUES (?,?,?,?,?,?)",
                               (case_key, c_id, doc_name, is_present, json.dumps(meta), datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()
    print("DB Created Successfully with Realistic Metadata")

if __name__ == "__main__":
    setup_final_comprehensive_db()