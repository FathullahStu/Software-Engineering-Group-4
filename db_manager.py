# FILE: db_manager.py
# Written by: Group 4 (Full Backend Integration)
# Purpose: Handles Database, Schema, Auth, and Business Logic for Gaps 1-5.

import sqlite3
import hashlib
import pandas as pd
import random
from datetime import datetime

DB_NAME = "ecosort.db"

# ==========================================
# 1. DATABASE CONNECTION & SETUP
# ==========================================
def create_connection():
    """Establishes a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    except sqlite3.Error as e:
        print(f"Error connecting to DB: {e}")
    return conn

def create_tables():
    """
    Creates the 5 Normalized Tables as per Documentation.
    """
    conn = create_connection()
    c = conn.cursor()

    # TABLE 1: USERS (Authentication & Role Base)
    # Includes 'assigned_zone' for Collectors (Gap 3)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        assigned_zone TEXT,  
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # TABLE 2: RESIDENT PROFILES (Specific to Residents)
    # Includes Address and Zone (Gap 4)
    c.execute('''CREATE TABLE IF NOT EXISTS resident_profiles (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        address TEXT NOT NULL,
        zone TEXT NOT NULL,
        current_points INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    # TABLE 3: PICKUP REQUESTS (Transactions)
    c.execute('''CREATE TABLE IF NOT EXISTS pickup_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER NOT NULL,
        waste_type TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        scheduled_date TEXT NOT NULL,
        weight_kg REAL DEFAULT 0.0,
        driver_id INTEGER,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resident_id) REFERENCES users (id),
        FOREIGN KEY (driver_id) REFERENCES users (id)
    )''')

    # TABLE 4: REWARDS CATALOG (Inventory)
    c.execute('''CREATE TABLE IF NOT EXISTS rewards_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        cost_points INTEGER NOT NULL,
        stock_level INTEGER DEFAULT 50,
        description TEXT
    )''')

    # TABLE 5: REDEMPTION LOGS (Audit Trail)
    c.execute('''CREATE TABLE IF NOT EXISTS redemption_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        points_spent INTEGER NOT NULL,
        redeemed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resident_id) REFERENCES users (id),
        FOREIGN KEY (item_id) REFERENCES rewards_catalog (id)
    )''')

    conn.commit()
    
    # Check if we need to seed data (if users table is empty)
    c.execute("SELECT count(*) FROM users")
    if c.fetchone()[0] == 0:
        seed_data(conn)
        
    conn.close()

# ==========================================
# 2. DATA SEEDING
# ==========================================
def seed_data(conn):
    """Populates the DB with initial consistent data."""
    c = conn.cursor()
    print("Seeding Normalized Database...")

    def hash_pw(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # 1. USERS
    users = [
        # Username, Password, Role, Assigned_Zone
        ("john", hash_pw("123"), "Resident", None),
        ("sarah", hash_pw("123"), "Resident", None),
        ("ali", hash_pw("123"), "Resident", None),
        ("fathul", hash_pw("123"), "Collector", "Zone A"), # Gap 3
        ("amir", hash_pw("123"), "Collector", "Zone B"),   # Gap 3
        ("afiq", hash_pw("123"), "Admin", None),
        ("min", hash_pw("123"), "Admin", None)
    ]
    c.executemany("INSERT INTO users (username, password, role, assigned_zone) VALUES (?, ?, ?, ?)", users)

    # 2. RESIDENT PROFILES (Gap 4: Real Addresses)
    c.execute("SELECT id, username FROM users WHERE role='Resident'")
    residents = c.fetchall()
    
    profiles_map = {
        "john": ("John Doe", "12 Jalan Teknokrat 3, Cyberjaya", "Zone A"),
        "sarah": ("Sarah Tan", "45 Persiaran Multimedia, Cyberjaya", "Zone B"),
        "ali": ("Ali bin Abu", "88 Lingkaran Cyber Point, Cyberjaya", "Zone A")
    }

    for res in residents:
        if res['username'] in profiles_map:
            name, addr, zone = profiles_map[res['username']]
            c.execute("INSERT INTO resident_profiles (user_id, full_name, address, zone, current_points) VALUES (?, ?, ?, ?, ?)", 
                      (res['id'], name, addr, zone, 50))

    # 3. REWARDS
    rewards = [
        ("GrabFood RM10 Voucher", 500, 50),
        ("TGV Cinema Ticket", 800, 30),
        ("Stainless Steel Straw Set", 200, 100),
        ("EcoSort T-Shirt", 1500, 20),
        ("Netflix 1-Month Sub", 1200, 15)
    ]
    c.executemany("INSERT INTO rewards_catalog (item_name, cost_points, stock_level) VALUES (?, ?, ?)", rewards)

    conn.commit()
    print("Database seeding complete.")

# ==========================================
# 3. AUTHENTICATION FUNCTIONS
# ==========================================
def login_user(username, password):
    conn = create_connection()
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute("SELECT id, username, role, assigned_zone FROM users WHERE username=? AND password=?", (username, hashed))
    user = c.fetchone()
    conn.close()
    return user

def register_user(username, password, role="Resident", address="Cyberjaya", zone="Zone A"):
    conn = create_connection()
    c = conn.cursor()
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Add to Users
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
        user_id = c.lastrowid
        
        # Add to Profiles if Resident
        if role == "Resident":
            c.execute("INSERT INTO resident_profiles (user_id, address, zone) VALUES (?, ?, ?)", 
                      (user_id, address, zone))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ==========================================
# 4. RESIDENT FUNCTIONS (Gaps 1, 2, 5)
# ==========================================
def get_user_points(username):
    conn = create_connection()
    c = conn.cursor()
    query = """
    SELECT p.current_points 
    FROM resident_profiles p
    JOIN users u ON u.id = p.user_id
    WHERE u.username = ?
    """
    c.execute(query, (username,))
    result = c.fetchone()
    conn.close()
    return result['current_points'] if result else 0

def add_booking(username, date, waste_type, notes=""):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user:
        c.execute("""
            INSERT INTO pickup_requests (resident_id, scheduled_date, waste_type, notes, status) 
            VALUES (?, ?, ?, ?, 'Pending')
        """, (user['id'], date, waste_type, notes))
        conn.commit()
    conn.close()

def get_resident_history(username):
    conn = create_connection()
    query = """
    SELECT r.scheduled_date as date, r.waste_type, r.status, r.weight_kg 
    FROM pickup_requests r
    JOIN users u ON u.id = r.resident_id
    WHERE u.username = ?
    ORDER BY r.scheduled_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df

# --- GAP 5: PROFILE MANAGEMENT ---
def get_resident_details(username):
    """Fetches profile details for editing."""
    conn = create_connection()
    c = conn.cursor()
    query = """
    SELECT p.full_name, p.address, p.zone
    FROM resident_profiles p
    JOIN users u ON u.id = p.user_id
    WHERE u.username = ?
    """
    c.execute(query, (username,))
    result = c.fetchone()
    conn.close()
    return result

def update_resident_profile(username, full_name, address):
    """Updates Resident's personal info."""
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user:
        try:
            c.execute("UPDATE resident_profiles SET full_name=?, address=? WHERE user_id=?", 
                     (full_name, address, user['id']))
            conn.commit()
            return True
        except:
            return False
    conn.close()
    return False

def update_password(username, new_password):
    """Updates User's password."""
    conn = create_connection()
    c = conn.cursor()
    hashed = hashlib.sha256(new_password.encode()).hexdigest()
    try:
        c.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# ==========================================
# 5. COLLECTOR FUNCTIONS (Gap 4)
# ==========================================
def get_pending_jobs(driver_zone=None):
    conn = create_connection()
    # Query fetches REAL Address and Zone from Profiles for Gap 4
    query = """
    SELECT 
        r.id, 
        u.username as resident_username, 
        p.address, 
        p.zone,
        r.waste_type, 
        r.scheduled_date as date, 
        r.notes as driver_notes
    FROM pickup_requests r
    JOIN users u ON u.id = r.resident_id
    JOIN resident_profiles p ON p.user_id = u.id
    WHERE r.status = 'Pending'
    """
    if driver_zone:
        query += f" AND p.zone = '{driver_zone}'"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def complete_job(job_id, weight):
    conn = create_connection()
    c = conn.cursor()
    
    # Update Booking
    c.execute("UPDATE pickup_requests SET status='Completed', weight_kg=? WHERE id=?", (weight, job_id))
    
    # Award Points (1kg = 10 pts)
    c.execute("SELECT resident_id FROM pickup_requests WHERE id=?", (job_id,))
    res_id = c.fetchone()['resident_id']
    points = int(weight * 10)
    c.execute("UPDATE resident_profiles SET current_points = current_points + ? WHERE user_id=?", (points, res_id))
    
    conn.commit()
    conn.close()

def report_issue(job_id, reason):
    """Use Case 9"""
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE pickup_requests SET status='Failed', notes=? WHERE id=?", (f"Issue: {reason}", job_id))
    conn.commit()
    conn.close()

# ==========================================
# 6. ADMIN FUNCTIONS (Gap 3)
# ==========================================
def get_all_users():
    conn = create_connection()
    query = """
    SELECT u.id, u.username, u.role, u.assigned_zone, p.current_points, p.zone as resident_zone
    FROM users u
    LEFT JOIN resident_profiles p ON u.id = p.user_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_employee_zone(username, new_zone):
    """Gap 3: Assign Collector to Zone."""
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET assigned_zone=? WHERE username=? AND role='Collector'", (new_zone, username))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_bookings_admin():
    conn = create_connection()
    query = """
    SELECT r.id, r.scheduled_date as date, u.username as resident_username, r.waste_type, r.status, r.weight_kg 
    FROM pickup_requests r
    JOIN users u ON u.id = r.resident_id
    ORDER BY r.scheduled_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==========================================
# 7. REWARDS FUNCTIONS
# ==========================================
def get_rewards_list():
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM rewards_catalog WHERE stock_level > 0", conn)
    conn.close()
    return df

def redeem_item(username, item_name, cost):
    conn = create_connection()
    c = conn.cursor()
    
    # User Check
    c.execute("SELECT u.id, p.current_points FROM users u JOIN resident_profiles p ON u.id = p.user_id WHERE u.username=?", (username,))
    user = c.fetchone()
    if not user: return False, "User not found"
    
    # Item Check
    c.execute("SELECT id, stock_level FROM rewards_catalog WHERE item_name=?", (item_name,))
    item = c.fetchone()
    if not item or item['stock_level'] < 1: return False, "Out of stock"
    if user['current_points'] < cost: return False, "Insufficient points"
    
    # Transaction
    try:
        c.execute("UPDATE resident_profiles SET current_points = current_points - ? WHERE user_id=?", (cost, user['id']))
        c.execute("UPDATE rewards_catalog SET stock_level = stock_level - 1 WHERE id=?", (item['id'],))
        c.execute("INSERT INTO redemption_logs (resident_id, item_id, points_spent) VALUES (?, ?, ?)", 
                  (user['id'], item['id'], cost))
        conn.commit()
        return True, f"CODE-{random.randint(100,999)}"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()