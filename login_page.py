# FILE: login_page.py
# Written by: Group 4 (Authentication Module)
# Purpose: Handles User Login & Registration with Address/Zone support (Gap 4).

import streamlit as st
import db_manager as db
import time
import os

def show_login_screen():
    """
    Renders the Login and Registration tabs.
    """
    # CENTERED CONTAINER
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # LOGO & BRANDING (FIXED: Now actually includes the image)
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_container_width=True)
        
        st.markdown("<h1 style='text-align: center; color: #2E7D32;'>♻️ EcoSort</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Smart Waste Management System</p>", unsafe_allow_html=True)
        
        # TABS
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        
        # ==========================================
        # TAB 1: LOGIN
        # ==========================================
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password.")
                    else:
                        # Attempt Login
                        user = db.login_user(username.lower(), password)
                        
                        if user:
                            # SUCCESS: SET SESSION STATE
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = user['username']
                            st.session_state['role'] = user['role']
                            
                            # GAP 3 FIX: Store assigned zone for Collectors
                            if user['role'] == 'Collector':
                                st.session_state['assigned_zone'] = user['assigned_zone']
                            else:
                                st.session_state['assigned_zone'] = None
                            
                            st.success(f"Welcome back, {user['username'].capitalize()}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Invalid Username or Password.")

        # ==========================================
        # TAB 2: REGISTER (Updated for Gap 4)
        # ==========================================
        with tab_register:
            st.markdown("### Create New Account")
            
            with st.form("register_form"):
                new_user = st.text_input("Choose Username")
                new_pass = st.text_input("Choose Password", type="password")
                role = st.selectbox("I am a...", ["Resident", "Collector", "Admin"])
                
                # --- NEW: ADDRESS FIELDS FOR RESIDENTS ---
                # These fields are visible to everyone but only required/saved if Role == Resident
                st.markdown("---")
                st.caption("📍 Resident Details (Required for Pickups)")
                address = st.text_input("Home Address", placeholder="e.g., 12 Jalan Teknokrat 3")
                zone = st.selectbox("Residential Zone", ["Zone A", "Zone B", "Zone C", "Zone D"])
                
                reg_submit = st.form_submit_button("Sign Up", use_container_width=True)
                
                if reg_submit:
                    # 1. Basic Validation
                    if not new_user or not new_pass:
                        st.warning("Username and Password are required.")
                    else:
                        # 2. Resident Validation (Must have Address)
                        if role == "Resident" and not address:
                            st.error("Residents must provide a valid address.")
                        else:
                            # 3. Attempt Registration
                            # We send address/zone only if resident, otherwise empty strings
                            final_addr = address if role == "Resident" else ""
                            final_zone = zone if role == "Resident" else ""
                            
                            success = db.register_user(
                                new_user.lower(), 
                                new_pass, 
                                role, 
                                final_addr, 
                                final_zone
                            )
                            
                            if success:
                                st.success("✅ Account created! Please log in.")
                                time.sleep(1)
                            else:
                                st.error("Username already exists. Try another.")

    # FOOTER
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: grey; font-size: 12px;'>Group 4 Project | Multimedia University</p>", unsafe_allow_html=True)