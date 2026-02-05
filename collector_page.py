# FILE: collector_page.py
# Written by: Group 4 (Fathullah)
# Purpose: Visually Enhanced Driver Dashboard with "Logistics" styling.

import streamlit as st
import pandas as pd
import db_manager as db
import random
import time

# Cyberjaya Center Coordinates (Approximate)
CENTER_LAT = 2.9213
CENTER_LON = 101.6559

def show():
    """
    Main function for the Collector Dashboard.
    """
    # 1. GET USER CONTEXT
    username = st.session_state.get('username', 'Driver')
    
    # ==========================================
    # 🎨 HERO SECTION (High-Vis Logistics Style)
    # ==========================================
    # We use Amber/Orange for that "Industrial/Safety" feel
    st.markdown(f"""
        <div style='background-color: #FF8F00; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='margin:0; color: white; font-family: sans-serif;'>🚛 LOGISTICS HUB: {username.upper()}</h2>
            <p style='margin:0; opacity: 0.9;'><b>Vehicle:</b> T-404 (5 Ton) | <b>Zone:</b> Cyberjaya Sector A | <b>Status:</b> 🟢 ON DUTY</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. MAIN TABS
    tab1, tab2 = st.tabs(["📋 Digital Manifest", "🗺️ Live GPS Navigation"])
    
    # Fetch real pending jobs from the database
    df = db.get_pending_jobs()
    
    # ==========================================
    # TAB 1: JOB LIST (The "Ticket" Look)
    # ==========================================
    with tab1:
        if df.empty:
            st.success("🎉 All Clear! No pending pickups. Return to base.")
            st.image("https://media.giphy.com/media/26u4lOMA8JKSnL9Uk/giphy.gif", width=200) # Optional fun GIF
        else:
            # Dashboard Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📦 **Load:** {len(df)} Stops")
            with col2:
                st.warning(f"⚖️ **Est. Weight:** {len(df) * 5} kg")
            with col3:
                st.error(f"⏱️ **Shift End:** 17:00") # Adds fake urgency

            st.markdown("### 🛑 Priority Pickup List")
            st.caption("Please load items carefully and weigh before confirmation.")
            
            # Iterate through jobs
            for index, row in df.iterrows():
                # Visual Trick: Use a container with a border to make it look like a physical "Ticket"
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        # Color-coded waste type badge using Streamlit magic text
                        badge_color = "red" if "E-Waste" in row['waste_type'] else "blue"
                        st.markdown(f":{badge_color}[**{row['waste_type']}**]")
                        
                        st.subheader(f"📍 Resident: {row['resident_username']}")
                        
                        # Generate a fake address for realism (since DB doesn't store addresses)
                        fake_address = f"Jalan Teknokrat {random.randint(1,6)}, Block {random.choice(['A','B','C'])}"
                        st.markdown(f"**Address:** {fake_address}")
                        
                        st.caption(f"📅 Scheduled: {row['date']} | 📝 Notes: {row['driver_notes'] or 'N/A'}")

                    with c2:
                        st.write("") # Spacer to push the input down visually
                        
                        # INPUT: Actual Weight collected
                        weight = st.number_input(
                            "Weight (kg)", 
                            min_value=0.1, 
                            value=2.0, 
                            step=0.5, 
                            key=f"w_{row['id']}"
                        )
                        
                        # BUTTON: Complete the Job
                        if st.button("✅ LOAD UNIT", key=f"btn_{row['id']}", type="primary", use_container_width=True):
                            # 1. Update DB
                            db.complete_job(row['id'], weight)
                            
                            # 2. Visual Feedback
                            st.toast(f"Unit loaded: {weight}kg. Route updated.")
                            time.sleep(0.5)
                            st.rerun() # Refresh to remove ticket

    # ==========================================
    # TAB 2: LIVE MAP (Tech Style)
    # ==========================================
    with tab2:
        st.subheader("🛰️ Satellite Navigation System")
        
        # LOGIC: Generate map points
        if df.empty:
            st.warning("⚠️ No active targets. Simulating sector scan...")
            # Generate 5 fake ghost points so the map isn't empty during demo
            map_data = pd.DataFrame({
                'lat': [CENTER_LAT + random.uniform(-0.015, 0.015) for _ in range(5)],
                'lon': [CENTER_LON + random.uniform(-0.015, 0.015) for _ in range(5)],
            })
        else:
            st.success(f"🔵 Routes Calculated: {len(df)} Active Targets")
            # Generate points for real jobs
            map_data = pd.DataFrame({
                'lat': [CENTER_LAT + random.uniform(-0.015, 0.015) for _ in range(len(df))],
                'lon': [CENTER_LON + random.uniform(-0.015, 0.015) for _ in range(len(df))],
            })
            
        # RENDER THE MAP
        st.map(map_data, zoom=13)
        
        # The "Cool Tech" Button for Demo
        col_btn, col_txt = st.columns([1, 2])
        with col_btn:
            if st.button("🔄 Optimize Route (AI)"):
                with st.status("Connecting to EcoSort Cloud...", expanded=True) as status:
                    time.sleep(1)
                    st.write("Analyzing Traffic Density...")
                    time.sleep(0.8)
                    st.write("Optimizing Fuel Efficiency...")
                    time.sleep(0.8)
                    status.update(label="✅ Route Optimized!", state="complete", expanded=False)
                st.success("New path loaded. Estimated time saved: 12 mins.")

# ==========================================
# TEST BLOCK (For Fathul/Amir Isolation Test)
# ==========================================
if __name__ == "__main__":
    # Mock Session State
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['username'] = "fathul"
        st.session_state['role'] = "Collector"

    # Mock Sidebar
    with st.sidebar:
        st.header("🚛 Driver Mode")
        st.write("User: Fathul")
        
    show()