# FILE: db_manager.py
# Written by: Group 4 (Backend)
# Purpose: Handles all database interactions (Users, Bookings, Points, Rewards).

import sqlite3
import pandas as pd

DB_NAME = "ecosort.db"

# =========================================================
# 1. SETUP & SEEDING (The Foundation)
# =========================================================

def create_connection():
    """Creates and returns a connection to the database."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def create_tables():
    """
    Creates the necessary tables if they don't exist.
    Also calls seed_data() to populate test accounts.
    """
    conn = create_connection()
    c = conn.cursor()
    
    # 1. USERS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            points INTEGER DEFAULT 0
        )
    ''')
    
    # 2. BOOKINGS TABLE (Waste Collection Requests)
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resident_username TEXT,
            date TEXT,
            waste_type TEXT,
            status TEXT DEFAULT 'Pending',
            weight_kg REAL DEFAULT 0.0,
            driver_notes TEXT DEFAULT ''
        )
    ''')
    
    # 3. REWARDS TABLE (Shop Items)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            cost INTEGER
        )
    ''')
    
    conn.commit()
    
    # Check if rewards exist, if not, add defaults
    c.execute('SELECT count(*) FROM rewards')
    if c.fetchone()[0] == 0:
        default_rewards = [
            ('Tesco RM10 Voucher', 500),
            ('GrabFood RM5 Discount', 250),
            ('Metal Straw Set', 100),
            ('EcoSort T-Shirt', 1000),
            ('Netflix 1-Month Sub', 1500)
        ]
        c.executemany('INSERT INTO rewards (item_name, cost) VALUES (?, ?)', default_rewards)
        conn.commit()
        print("✅ Default rewards added.")

    conn.close()
    
    # TRIGGER SEED DATA
    seed_data()

def seed_data():
    """
    Automatically registers the Group 4 members and test users
    so you don't have to sign up manually.
    """
    # Format: (username, password, role)
    # NOTE: Password is set to '123' for everyone for easy testing.
    test_users = [
        ("afiq",   "123", "Admin"),
        ("min",    "123", "Admin"),
        ("fathul", "123", "Collector"),
        ("amir",   "123", "Collector"),
        ("john",   "123", "Resident")
    ]
    
    conn = create_connection()
    c = conn.cursor()
    
    for user, pwd, role in test_users:
        try:
            # Try to insert. If username exists, it will fail silently (which is good).
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (user, pwd, role))
            print(f"✅ Created Seed Account: {user} ({role})")
        except sqlite3.IntegrityError:
            pass # User already exists, skip
            
    conn.commit()
    conn.close()

# =========================================================
# 2. AUTHENTICATION (Login & Sign Up)
# =========================================================

def login_check(username, password):
    """
    Verifies credentials. Returns the ROLE if successful, else None.
    """
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT role FROM users WHERE username = ? AND password = ?', (username, password))
    result = c.fetchone()
    conn.close()
    
    if result:
        return result[0]  # Return the role (e.g., "Resident")
    return None

def add_user(username, password, role):
    """
    Registers a new user. Returns True if successful, False if username taken.
    """
    conn = create_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# =========================================================
# 3. RESIDENT FUNCTIONS
# =========================================================

def add_booking(username, date, waste_type):
    """Adds a new waste collection request."""
    conn = create_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings (resident_username, date, waste_type, status)
        VALUES (?, ?, ?, 'Pending')
    ''', (username, date, waste_type))
    conn.commit()
    conn.close()

def get_resident_history(username):
    """Returns a DataFrame of the user's past bookings."""
    conn = create_connection()
    query = "SELECT * FROM bookings WHERE resident_username = ? ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df

def get_user_points(username):
    """Returns the current point balance for a user."""
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT points FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_rewards_list():
    """Returns a DataFrame of all available rewards."""
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM rewards", conn)
    conn.close()
    return df

def redeem_item(username, item_name, cost):
    """
    Deducts points and returns a success message/voucher code.
    """
    current_pts = get_user_points(username)
    
    if current_pts >= cost:
        conn = create_connection()
        c = conn.cursor()
        # Deduct points
        c.execute('UPDATE users SET points = points - ? WHERE username = ?', (cost, username))
        conn.commit()
        conn.close()
        
        # Generate a fake voucher code
        import random
        code = f"ECO-{random.randint(1000,9999)}"
        return True, code
    else:
        return False, "Not enough points!"

# =========================================================
# 4. COLLECTOR FUNCTIONS
# =========================================================

def get_pending_jobs():
    """Returns all bookings with status 'Pending'."""
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM bookings WHERE status = 'Pending'", conn)
    conn.close()
    return df

def complete_job(job_id, weight):
    """
    Marks a job as Completed, records weight, and awards points to the Resident.
    Formula: 1 kg = 10 Points.
    """
    points_to_add = int(weight * 10)
    
    conn = create_connection()
    c = conn.cursor()
    
    # 1. Get the resident name from the booking
    c.execute('SELECT resident_username FROM bookings WHERE id = ?', (job_id,))
    res = c.fetchone()
    
    if res:
        resident_name = res[0]
        
        # 2. Update Booking Status
        c.execute('''
            UPDATE bookings 
            SET status = 'Completed', weight_kg = ? 
            WHERE id = ?
        ''', (weight, job_id))
        
        # 3. Give Points to Resident
        c.execute('''
            UPDATE users 
            SET points = points + ? 
            WHERE username = ?
        ''', (points_to_add, resident_name))
        
        conn.commit()
    
    conn.close()

# =========================================================
# 5. ADMIN FUNCTIONS
# =========================================================

def get_all_users():
    """Returns all registered users."""
    conn = create_connection()
    df = pd.read_sql_query("SELECT id, username, role, points FROM users", conn)
    conn.close()
    return df

def get_all_bookings_admin():
    """Returns ALL bookings (history + pending) for analytics."""
    conn = create_connection()
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()
    return df