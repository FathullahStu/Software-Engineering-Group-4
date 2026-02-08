import streamlit as st
import db_manager as db
import os
import time

import login_page
import resident_page
import collector_page
import admin_page


st.set_page_config(
    page_title="EcoSort - Smart Waste Management",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_custom_css():
    """
    Injects CSS to style the app with a Dark Maroon sidebar.
    """
    st.markdown("""
        <style>
        /* 1. HIDE STREAMLIT BRANDING */
        #MainMenu {visibility: hidden;} /* Hides the 3-dot menu */
        footer {visibility: hidden;}    /* Hides 'Made with Streamlit' */
        /* header {visibility: hidden;}  <-- REMOVED: This was hiding the sidebar toggle! */
        
        /* Optional: Make the header transparent so it looks cleaner */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }
        
        /* 2. ROUNDED BUTTONS */
        .stButton button {
            border-radius: 20px;
            font-weight: 600;
        }
        
        /* 3. SIDEBAR STYLING (Dark Maroon) */
        [data-testid="stSidebar"] {
            background-color: #4a0404; /* Deep Maroon */
            border-right: 1px solid #750000;
        }
        
        /* 4. FORCE WHITE TEXT IN SIDEBAR */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label {
            color: #ffffff !important;
        }
        
        /* 5. METRIC CARDS BORDER */
        [data-testid="stMetricValue"] {
            font-size: 24px;
        }
        </style>
    """, unsafe_allow_html=True)


def init_system():
    # Create tables and Seed Data
    db.create_tables()
    
    # Initialize Session State
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'role' not in st.session_state:
        st.session_state['role'] = None

# Run initialization immediately
init_system()


def show_sidebar():
    """
    Displays the sidebar with Role-Specific Context (HUD).
    """
    with st.sidebar:
       
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_container_width=True)
        else:
            
            st.markdown("<h1 style='color: white;'>♻️ EcoSort</h1>", unsafe_allow_html=True)
        
        st.divider()

        
        if st.session_state['logged_in']:
            role = st.session_state['role']
            user = st.session_state['username']
            
           
            st.markdown(f"**👤 {role.upper()}**")
            st.caption(f"Logged in as: {user}")
            
            st.divider()
            
            
            if role == "Resident":
                points = db.get_user_points(user)
                st.markdown("### 🌱 Eco-Wallet")
                st.metric("Balance", f"{points} pts")
                st.success("Level 2 Status") 
                
                st.info("💡 **Daily Tip:**\nRinse plastic bottles to prevent contamination!")
            
            
            elif role == "Collector":
                st.markdown("### 🚛 Shift Details")
                st.write("**Vehicle:** T-404 (5 Ton)")
                st.write("**Zone:** Cyberjaya Sector A")
                
                
                st.success("☁️ Weather: Clear")
                st.warning("🚦 Traffic: Moderate")
            
            
            elif role == "Admin":
                st.markdown("### 🖥️ System Health")
                col1, col2 = st.columns(2)
                col1.metric("CPU", "12%")
                col2.metric("Mem", "48%")
                
                st.caption("✅ Database: Connected")
                st.caption("✅ API Gateway: Online")
                st.caption(f"🕒 Server Time: {time.strftime('%H:%M')}")

            st.divider()
            
            
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['role'] = None
                st.rerun()

        
        else:
            st.markdown("### Welcome Guest")
            st.info("Please log in to access the Smart Waste Management System.")
            st.markdown("---")
            st.caption("Group 4 Project\n(Afiq, Min, Amir, Fathullah)")


def main():
    """
    Directs the user to the correct page based on their Role.
    """
    # 1. load CSS
    load_custom_css()
    
    # 2. Show Sidebar
    show_sidebar()
    
    # 3. Check Login State
    if not st.session_state['logged_in']:
        login_page.show_login_screen()
        
    else:
        # User is logged in, check Role
        role = st.session_state['role']
        
        if role == "Resident":
            resident_page.show()
            
        elif role == "Collector":
            collector_page.show()
            
        elif role == "Admin":
            admin_page.show()
            
        else:
            st.error(f"⚠️ System Error: Unknown Role '{role}'. Please contact support.")


if __name__ == "__main__":
    main()