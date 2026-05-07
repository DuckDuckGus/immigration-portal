import sqlite3
import os
import json
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

def setup_final_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- TABLE STRUCTURE ---
    cursor.execute("CREATE TABLE Users (user_id INTEGER PRIMARY KEY, full_name TEXT, role TEXT)")
    cursor.execute("CREATE TABLE Clients (client_id INTEGER PRIMARY KEY, full_name TEXT, nationality TEXT, email TEXT)")
    cursor.execute("CREATE TABLE Case_Files (case_key TEXT PRIMARY KEY, client_id INTEGER, lawyer_id INTEGER, case_type TEXT, status TEXT)")
    
    # The Vault with JSON metadata and Quality Control columns
    cursor.execute("""
    CREATE TABLE Document_Vault (
        doc_id INTEGER PRIMARY KEY,
        case_key TEXT,
        doc_type TEXT,
        is_present BOOLEAN,
        file_format TEXT,
        scan_quality TEXT,
        metadata TEXT, 
        updated_at DATETIME,
        FOREIGN KEY(case_key) REFERENCES Case_Files(case_key)
    )""")

    # --- SEEDING CORE DATA ---
    lawyers = [(1, "Elena Ruiz-Castellanos", "Lawyer"), (2, "Iñigo Larrea", "Lawyer"), (3, "Admin User", "Admin")]
    cursor.executemany("INSERT INTO Users VALUES (?,?,?)", lawyers)

    countries = ["USA", "Philippines", "UK", "China", "Canada", "Brazil"]
    visa_types = ["Digital Nomad Visa", "Student Visa", "Non-Lucrative Residency", "Highly Skilled Professional"]

    for i in range(1, 12):
        client_name = fake.name()
        nationality = random.choice(countries)
        cursor.execute("INSERT INTO Clients (full_name, nationality, email) VALUES (?,?,?)", 
                       (client_name, nationality, fake.email()))
        client_id = cursor.lastrowid
        
        case_key = f"ES-2026-{2000+i}"
        visa = random.choice(visa_types)
        cursor.execute("INSERT INTO Case_Files VALUES (?,?,?,?,?)", 
                       (case_key, client_id, random.choice([1, 2]), visa, "In Progress"))

        # --- GENERATING DEEP METADATA PER DOC TYPE ---
        doc_list = ["Passport", "Police Certificate", "Health Insurance", "Bank Statements", "Medical Certificate"]
        
        for d in doc_list:
            is_present = random.choice([0, 1])
            meta = {}
            fmt = "PDF" if random.random() > 0.1 else "JPG" # Simulate rare incorrect format
            quality = random.choice(["High", "Medium", "Blurry"])

            if is_present:
                if d == "Police Certificate":
                    issue = (datetime.now() - timedelta(days=random.randint(10, 150))).strftime("%Y-%m-%d")
                    meta = {
                        "issue_date": issue,
                        "has_apostille": random.choice([True, False]),
                        "is_sworn_translated": random.choice([True, True, False]), # Mostly true
                        "issuing_authority": "Federal Bureau",
                        "validity_months": 3 if nationality != "UK" else 6
                    }
                elif d == "Passport":
                    expiry = (datetime.now() + timedelta(days=random.randint(-30, 1500))).strftime("%Y-%m-%d")
                    meta = {
                        "expiry_date": expiry,
                        "passport_number": fake.bothify(text='??#######'),
                        "all_pages_scanned": random.choice([True, False]),
                        "blank_pages_count": random.randint(0, 10)
                    }
                elif d == "Health Insurance":
                    meta = {
                        "provider": random.choice(["Sanitas", "Adeslas", "DKV"]),
                        "no_copay": random.choice([True, True, False]),
                        "repatriation_included": True,
                        "policy_start": "2026-01-01"
                    }
                elif d == "Bank Statements":
                    meta = {
                        "balance_eur": random.randint(28000, 55000),
                        "period_months": 3,
                        "has_bank_stamp": random.choice([True, False]),
                        "currency": "EUR"
                    }
                elif d == "Medical Certificate":
                    meta = {
                        "official_template_used": random.choice([True, False]),
                        "doctor_registration_num": fake.bothify(text='#####'),
                        "issue_date": datetime.now().strftime("%Y-%m-%d")
                    }

            cursor.execute("""
                INSERT INTO Document_Vault (case_key, doc_type, is_present, file_format, scan_quality, metadata, updated_at) 
                VALUES (?,?,?,?,?,?,?)""",
                (case_key, d, is_present, fmt, quality, json.dumps(meta), datetime.now().isoformat())
            )

    conn.commit()
    conn.close()
    print(f"Database Revamped: {DB_PATH}")
    print("Deep Metadata active for: Expiry, Apostilles, Insurance Specs, and Scan Quality.")

if __name__ == "__main__":
    setup_final_db()