# FILE: login_page.py
# Written by: Group 4 (Min)
# Purpose: Handles User Authentication (Login & Registration) with validation.

import streamlit as st
import db_manager as db
import time
import os

def show_login_screen():
    """
    Displays the Authentication Interface.
    """
    
    # 1. HEADER & BRANDING
    # We use columns to center the logo or text
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Check if logo exists, otherwise show text
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center;'>♻️ EcoSort</h1>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center; color: gray;'>Smart Waste Management System</p>", unsafe_allow_html=True)
        st.divider()

    # 2. AUTHENTICATION TABS
    login_tab, register_tab = st.tabs(["🔐 Login", "📝 Register New User"])

    # ==========================================
    # TAB 1: LOGIN (Main Entry)
    # ==========================================
    with login_tab:
        st.write("") # Spacer
        
        with st.form(key='login_form'):
            # Input Fields
            username_input = st.text_input("Username", placeholder="e.g. john")
            password_input = st.text_input("Password", type="password", placeholder="e.g. 123")
            
            # Login Button
            submit_login = st.form_submit_button("Log In", type="primary", use_container_width=True)
            
            if submit_login:
                # A. Sanitize Inputs (Trim spaces)
                clean_user = username_input.strip().lower() # Case-insensitive username
                clean_pass = password_input.strip()
                
                # B. Validation
                if not clean_user or not clean_pass:
                    st.warning("⚠️ Please fill in both username and password.")
                else:
                    # C. Check Database
                    role = db.login_check(clean_user, clean_pass)
                    
                    if role:
                        # SUCCESS!
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = clean_user
                        st.session_state['role'] = role
                        
                        st.success(f"✅ Login successful! Welcome, {role}.")
                        time.sleep(0.5) # Smooth transition
                        st.rerun()      # Reload app to show Dashboard
                    else:
                        # FAIL
                        st.error("❌ Incorrect username or password.")

    # ==========================================
    # TAB 2: REGISTRATION (New Accounts)
    # ==========================================
    with register_tab:
        st.write("") # Spacer
        
        with st.form(key='register_form'):
            st.info("Create a new account to join the EcoSort community.")
            
            new_user = st.text_input("Choose a Username")
            new_pass = st.text_input("Choose a Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            
            # Role Selection
            st.write("Select Account Type:")
            role_choice = st.selectbox("Role", ["Resident", "Collector", "Admin"], label_visibility="collapsed")
            
            submit_reg = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit_reg:
                # A. Sanitize
                clean_new_user = new_user.strip().lower()
                clean_new_pass = new_pass.strip()
                clean_confirm = confirm_pass.strip()
                
                # B. Validation Logic
                if not clean_new_user or not clean_new_pass:
                    st.warning("⚠️ Username and Password cannot be empty.")
                elif clean_new_pass != clean_confirm:
                    st.error("❌ Passwords do not match.")
                else:
                    # C. Attempt Registration in DB
                    success = db.add_user(clean_new_user, clean_new_pass, role_choice)
                    
                    if success:
                        st.success(f"🎉 Account created for {clean_new_user}! Please switch to the 'Login' tab.")
                        st.balloons()
                    else:
                        st.error("❌ That username is already taken. Please try a different one.")

# ==========================================
# TEST BLOCK (For Testing Isolation)
# ==========================================
if __name__ == "__main__":
    # This allows you to run "python -m streamlit run login_page.py"
    # just to test the look and feel of the login screen.
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        
    show_login_screen()