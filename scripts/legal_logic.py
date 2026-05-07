import sqlite3
import os
import json
from faker import Faker
import random
from datetime import datetime

fake = Faker('es_ES')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

def setup_data_driven_db():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- 1. THE STATUTE BOOK (Engagement Types) ---
    cursor.execute("""
    CREATE TABLE Engagement_Types (
        engagement_id INTEGER PRIMARY KEY,
        visa_name TEXT,
        required_docs TEXT -- Stored as JSON list
    )""")

    visa_rules = [
        (1, "Student Visa", json.dumps(["Passport", "Letter of Acceptance", "Bank Statements", "Health Insurance", "Police Certificate"])),
        (2, "Non-Lucrative Residency", json.dumps(["Passport", "Bank Statements", "Private Spanish Health Insurance", "Police Certificate", "Official Medical Certificate"])),
        (3, "Digital Nomad Visa", json.dumps(["Passport", "Work Contract", "Proof of Income", "Police Certificate", "Social Security Certificate"]))
    ]
    cursor.executemany("INSERT INTO Engagement_Types VALUES (?,?,?)", visa_rules)

    # --- 2. USERS, CLIENTS, CASE FILES ---
    cursor.execute("CREATE TABLE Users (user_id INTEGER PRIMARY KEY, full_name TEXT, role TEXT)")
    cursor.execute("CREATE TABLE Clients (client_id INTEGER PRIMARY KEY, full_name TEXT, nationality TEXT, email TEXT)")
    cursor.execute("CREATE TABLE Case_Files (case_key TEXT PRIMARY KEY, client_id INTEGER, lawyer_id INTEGER, engagement_id INTEGER, status TEXT)")
    cursor.execute("""
    CREATE TABLE Document_Vault (
        doc_id INTEGER PRIMARY KEY, case_key TEXT, doc_type TEXT, is_present BOOLEAN, metadata TEXT, updated_at DATETIME
    )""")

    # Seed 5 Lawyers
    lawyers = [(1, "Elena Ruiz", "Lawyer"), (2, "Iñigo Larrea", "Lawyer"), (3, "Javi Montoya", "Lawyer"), (4, "Bea Iglesia", "Lawyer"), (5, "Admin", "Admin")]
    cursor.executemany("INSERT INTO Users VALUES (?,?,?)", lawyers)

    # Seed 50 Cases
    for i in range(1, 51):
        last_name = fake.last_name()
        cursor.execute("INSERT INTO Clients (full_name, nationality, email) VALUES (?,?,?)", (f"{fake.first_name()} {last_name}", "USA", fake.email()))
        client_id = cursor.lastrowid
        
        eng_id = random.randint(1, 3) # Randomly assign one of our 3 visa types
        case_key = f"{last_name.upper().replace(' ', '_')}_2026_{100+i}"
        cursor.execute("INSERT INTO Case_Files VALUES (?,?,?,?,?)", (case_key, client_id, random.randint(1, 4), eng_id, "In Progress"))

        # --- 3. DYNAMIC VAULT POPULATION ---
        # Look up what is needed for THIS engagement
        cursor.execute("SELECT required_docs FROM Engagement_Types WHERE engagement_id = ?", (eng_id,))
        required_list = json.loads(cursor.fetchone()[0])

        for doc_name in required_list:
            is_present = random.choice([0, 1])
            # If present, give it metadata; if not, all NULLs as requested
            meta = {"issue_date": "2026-01-01", "has_apostille": True} if is_present else {"issue_date": None, "has_apostille": None}
            
            cursor.execute("INSERT INTO Document_Vault (case_key, doc_type, is_present, metadata, updated_at) VALUES (?,?,?,?,?)",
                           (case_key, doc_name, is_present, json.dumps(meta), datetime.now().isoformat()))

    conn.commit()
    conn.close()
    print("Data-Driven Database Setup Complete.")

if __name__ == "__main__":
    setup_data_driven_db()