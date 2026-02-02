# FILE: db_manager.py
# Written by: Group 4 (Min)
# Purpose: Handles all database connections so the main app is clean.

import sqlite3
import pandas as pd
from datetime import datetime, date
import random

# The name of our database file
DB_NAME = "waste.db"

# ====================================================
# 1. SETUP SECTION (Run this to build the database)
# ====================================================

def create_tables():
    """
    Creates the necessary tables if they don't exist yet.
    We call this in app.py every time the app starts, just to be safe.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. USERS TABLE (Stores Residents, Collectors, and Admins)
    # We use 'username' as the unique ID for simplicity
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        points INTEGER DEFAULT 0
    )''')

    # 2. BOOKINGS TABLE (The pickup requests)
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_username TEXT,
        date TEXT,
        waste_type TEXT,
        weight_kg REAL DEFAULT 0.0,
        status TEXT,
        notes TEXT
    )''')

    # 3. REWARDS TABLE (The items people can buy)
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        cost INTEGER
    )''')

    # 4. REDEMPTION HISTORY (To track who bought what)
    c.execute('''CREATE TABLE IF NOT EXISTS redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        item_name TEXT,
        redeemed_at TEXT,
        voucher_code TEXT
    )''')

    # --- POPULATE DEFAULT DATA (So the app isn't empty) ---
    
    # Check if rewards exist, if not, add them
    c.execute("SELECT count(*) FROM rewards")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO rewards (item_name, cost) VALUES (?, ?)", ("RM5 Grocery Voucher", 50))
        c.execute("INSERT INTO rewards (item_name, cost) VALUES (?, ?)", ("Metal Straw Set", 100))
        c.execute("INSERT INTO rewards (item_name, cost) VALUES (?, ?)", ("RM20 Supermarket Voucher", 200))
        c.execute("INSERT INTO rewards (item_name, cost) VALUES (?, ?)", ("Exclusive T-Shirt", 500))
    
    # Check if Admin exists, if not, add one
    c.execute("SELECT count(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "Admin"))

    conn.commit()
    conn.close()

# ====================================================
# 2. AUTHENTICATION SECTION (Login/Signup)
# ====================================================

def login_check(username, password):
    """
    Checks if username and password match.
    Returns the ROLE (e.g., 'Resident') if valid, or None if invalid.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    
    if result:
        return result[0]  # Return the role string
    else:
        return None

def add_user(username, password, role):
    """
    Registers a new user. Returns True if successful, False if username taken.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role, points) VALUES (?, ?, ?, 0)", 
                  (username, password, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists

# ====================================================
# 3. RESIDENT FEATURES (Booking & Points)
# ====================================================

def add_booking(username, date_str, waste_type):
    """
    Adds a new 'Pending' booking for a resident.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO bookings (resident_username, date, waste_type, status, weight_kg) VALUES (?, ?, ?, ?, 0)", 
              (username, date_str, waste_type, "Pending"))
    conn.commit()
    conn.close()

def get_resident_history(username):
    """
    Returns a dataframe of all bookings for one specific resident.
    """
    conn = sqlite3.connect(DB_NAME)
    # We use pandas here because it's easier to show in Streamlit
    df = pd.read_sql_query("SELECT id, date, waste_type, status, weight_kg FROM bookings WHERE resident_username = ?", 
                           conn, params=(username,))
    conn.close()
    return df

def get_user_points(username):
    """
    Gets the current point balance for a user.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_rewards_list():
    """
    Returns the list of things people can buy.
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM rewards", conn)
    conn.close()
    return df

def redeem_item(username, item_name, cost):
    """
    Handles the purchase.
    1. Checks if user has enough points.
    2. Deducts points.
    3. Generates a voucher code.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check current points first
    c.execute("SELECT points FROM users WHERE username=?", (username,))
    current_points = c.fetchone()[0]
    
    if current_points >= cost:
        # Deduct points
        new_points = current_points - cost
        c.execute("UPDATE users SET points=? WHERE username=?", (new_points, username))
        
        # Generate a fake code (e.g., REWARD-8374)
        code = f"REWARD-{random.randint(1000, 9999)}"
        
        # Log the transaction
        c.execute("INSERT INTO redemptions (username, item_name, redeemed_at, voucher_code) VALUES (?, ?, ?, ?)",
                  (username, item_name, datetime.now().strftime("%Y-%m-%d"), code))
        
        conn.commit()
        conn.close()
        return True, code
    else:
        conn.close()
        return False, "Not enough points"

# ====================================================
# 4. COLLECTOR FEATURES (Driver Tools)
# ====================================================

def get_pending_jobs():
    """
    Returns all bookings that are still 'Pending'.
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM bookings WHERE status='Pending'", conn)
    conn.close()
    return df

def complete_job(booking_id, weight):
    """
    Driver marks a job as done.
    1. Updates status to 'Completed'.
    2. Updates weight.
    3. Calculates points (1 kg = 10 points) and gives them to the Resident.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Update Booking
    c.execute("UPDATE bookings SET status='Completed', weight_kg=? WHERE id=?", (weight, booking_id))
    
    # 2. Find who booked it
    c.execute("SELECT resident_username FROM bookings WHERE id=?", (booking_id,))
    resident_name = c.fetchone()[0]
    
    # 3. Give Points (Simple Formula: Weight * 10)
    points_earned = int(weight * 10)
    c.execute("UPDATE users SET points = points + ? WHERE username=?", (points_earned, resident_name))
    
    conn.commit()
    conn.close()

# ====================================================
# 5. ADMIN FEATURES (Analytics)
# ====================================================

def get_all_bookings_admin():
    """
    Returns EVERYTHING for the admin dashboard.
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM bookings", conn)
    conn.close()
    return df

def get_all_users():
    """
    Returns list of all users.
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, username, role, points FROM users", conn)
    conn.close()
    return df

# ====================================================
# 6. INITIALIZATION BLOCK
# ====================================================
# This runs if you type "python db_manager.py" in the terminal.
# It's a quick way to reset/start the DB.
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
    print("Default Admin User created: username='admin', password='admin123'")