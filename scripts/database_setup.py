import sqlite3
from faker import Faker
import random
import os
import re
import unicodedata

# 1. FIXED PATHING
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'portal.db'))

# We use two fakers: one for Spanish names/phones, one for English country names
fake_es = Faker('es_ES')
fake_en = Faker('en_US') 

NUM_LAWYERS = 5
NUM_CASES = 50

CASE_TYPES = [
    "Student Visa", "Non-Lucrative Residency", "EU Family Members",
    "Work permit – Employee", "Highly Skilled Professional", "EU Blue Card",
    "Digital Nomad", "Work permit – Self Employed",
    "Visa for Content Creators & Influencers", "Professional Athletes"
]

def slugify_name(name):
    """Converts 'Mónica García-López' to 'MONICA_GARCIA_LOPEZ'"""
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\s-]', '', name).strip().upper()
    return re.sub(r'[-\s]+', '_', name)

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # Drop and Recreate tables
    cursor.execute("DROP TABLE IF EXISTS Document_Vault")
    cursor.execute("DROP TABLE IF EXISTS Case_Files")
    cursor.execute("DROP TABLE IF EXISTS Clients")
    cursor.execute("DROP TABLE IF EXISTS Users")

    cursor.execute('''CREATE TABLE Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        full_name TEXT,
        password_hash TEXT,
        role TEXT,
        preferred_lang TEXT DEFAULT 'EN'
    )''')

    cursor.execute('''CREATE TABLE Clients (
        client_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        dob DATE,
        nationality TEXT,
        entry_date DATE,
        immigration_status TEXT,
        phone_number TEXT,
        email TEXT,
        monthly_income REAL
    )''')

    cursor.execute('''CREATE TABLE Case_Files (
        case_key TEXT PRIMARY KEY,
        client_id INTEGER,
        lawyer_id INTEGER,
        case_type TEXT,
        status TEXT,
        FOREIGN KEY(client_id) REFERENCES Clients(client_id),
        FOREIGN KEY(lawyer_id) REFERENCES Users(user_id)
    )''')

    cursor.execute('''CREATE TABLE Document_Vault (
        doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_key TEXT,
        doc_type TEXT,
        file_path TEXT,
        is_present BOOLEAN,
        FOREIGN KEY(case_key) REFERENCES Case_Files(case_key)
    )''')

    try:
        # Admin User
        cursor.execute("INSERT INTO Users (username, full_name, password_hash, role, preferred_lang) VALUES (?,?,?,?,?)",
                       ('admin_boss', 'Administrator', 'hash123', 'Admin', 'EN'))
    
        lawyers_data = [
            ('elena_ruiz', 'Elena Ruiz-Castellanos'),
            ('inigo_arretxea', 'Iñigo Arretxea'),
            ('sofia_silva', 'Sofia Silva'),
            ('mateo_fernandez', 'Mateo Fernández'),
            ('lucia_ortiz', 'Lucia Ortiz')
        ]

        lawyer_ids = []
        for username, lawyer_full_name in lawyers_data:
            cursor.execute("INSERT INTO Users (username, full_name, password_hash, role, preferred_lang) VALUES (?,?,?,?,?)",
                           (username, lawyer_full_name, 'hash123', 'Lawyer', 'ES'))
            lawyer_ids.append(cursor.lastrowid)
    
        # Generate Cases
        for _ in range(NUM_CASES):
            client_full_name = fake_es.name()
            clean_name = slugify_name(client_full_name)
            
            # KEY CHANGE: Using fake_en.country() for English nationality values
            nationality_en = fake_en.country()

            cursor.execute('''INSERT INTO Clients (full_name, dob, nationality, entry_date, immigration_status, phone_number, email, monthly_income)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (client_full_name, 
                            fake_es.date_of_birth(minimum_age=18, maximum_age=65).isoformat(), 
                            nationality_en, # Now in English
                            fake_es.date_between('-2y', 'today').strftime('%Y-%m-%d'), 
                            "In Process",
                            fake_es.phone_number(), 
                            fake_es.email(), 
                            random.uniform(1500, 5000)))
            
            client_id = cursor.lastrowid
            assigned_lawyer = random.choice(lawyer_ids)
            case_type = random.choice(CASE_TYPES)
            case_key = f"{clean_name}-2026-{case_type.split()[-1].upper()}"
    
            cursor.execute("INSERT INTO Case_Files VALUES (?, ?, ?, ?, ?)", 
                           (case_key, client_id, assigned_lawyer, case_type, "Active"))
    
            for doc in ["Passport", "Criminal_Records", "Entry_Proof", "Health_Insurance", "Application_Fee"]:
                file_path = f"/vault/{clean_name}_{doc}.pdf"
                cursor.execute("INSERT INTO Document_Vault (case_key, doc_type, file_path, is_present) VALUES (?, ?, ?, ?)",
                               (case_key, doc, file_path, random.choice([True, False])))
    
        conn.commit()
        print(f"DATABASE RECREATED SUCCESSFULLY WITH ENGLISH NATIONALITIES AT: {DB_PATH}")
        
    except Exception as e:
        conn.rollback()
        print(f"Failed to inject data! Rolled back transaction. Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()