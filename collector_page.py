# FILE: collector_page.py
# Written by: Group 4 (Fathullah)
# Purpose: Collector Dashboard with Real Addresses, Logical Maps, and Zone Filtering.

import streamlit as st
import pandas as pd
import db_manager as db
import random
import time

# ==========================================
# 📍 ZONE LOGIC (For Consistent Maps)
# ==========================================
# We define center points for each zone so the dots look logical
ZONE_CENTERS = {
    "Zone A": {"lat": 2.921300, "lon": 101.655900}, # Cyberjaya Core
    "Zone B": {"lat": 2.925000, "lon": 101.650000}, # Shaftsbury area
    "Zone C": {"lat": 2.918000, "lon": 101.660000}, # D'Pulze area
    "Zone D": {"lat": 2.930000, "lon": 101.645000}  # Outer rim
}

def get_stable_coords(username, zone):
    """
    Returns a fixed latitude/longitude for a specific user.
    This ensures 'John' always appears at the same house location,
    fixing the 'jumping dots' issue (Task 4).
    """
    # 1. Use the username to create a unique number (Seed)
    # This means 'john' always produces the same random numbers
    seed_val = sum(ord(c) for c in username)
    random.seed(seed_val)

    # 2. Get the center of their Zone
    center = ZONE_CENTERS.get(zone, ZONE_CENTERS["Zone A"])

    # 3. Add a small 'Jitter' so neighbors aren't stacked exactly on top of each other
    lat_offset = random.uniform(-0.003, 0.003)
    lon_offset = random.uniform(-0.003, 0.003)
    
    # 4. Calculate Final Coords
    final_lat = center["lat"] + lat_offset
    final_lon = center["lon"] + lon_offset

    # 5. Reset random seed so we don't affect other parts of the app
    random.seed(time.time())
    
    return final_lat, final_lon

# ==========================================
# MAIN VIEW
# ==========================================
def show():
    # 1. GET CONTEXT
    username = st.session_state.get('username', 'Driver')
    
    # Try to get the assigned zone from session state (if set by login)
    # If not found, we don't filter (show all)
    assigned_zone = st.session_state.get('assigned_zone', None)
    
    zone_display = assigned_zone if assigned_zone else "ALL ZONES"
    
    # 2. HERO SECTION
    st.markdown(f"""
        <div style='background-color: #FF8F00; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='margin:0; color: white; font-family: sans-serif;'>🚛 LOGISTICS HUB: {username.upper()}</h2>
            <p style='margin:0; opacity: 0.9;'><b>Vehicle:</b> T-404 (5 Ton) | <b>Zone:</b> {zone_display} | <b>Status:</b> 🟢 ON DUTY</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 3. FETCH DATA (Real Data from DB)
    # We pass the assigned_zone to filter jobs (Gap 3 Logic)
    df = db.get_pending_jobs(driver_zone=assigned_zone)
    
    tab1, tab2 = st.tabs(["📋 Digital Manifest", "🗺️ Live GPS Navigation"])
    
    # ==========================================
    # TAB 1: MANIFEST (Real Addresses - Gap 4)
    # ==========================================
    with tab1:
        if df.empty:
            st.success("🎉 All Clear! No pending pickups in your sector.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1: st.info(f"📦 **Load:** {len(df)} Stops")
            with col2: st.warning(f"⚖️ **Est. Weight:** {len(df) * 5} kg")
            with col3: st.error(f"⏱️ **Shift End:** 17:00")

            st.markdown("### 🛑 Priority Pickup List")
            
            for index, row in df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        badge_color = "red" if "E-Waste" in row['waste_type'] else "blue"
                        st.markdown(f":{badge_color}[**{row['waste_type']}**]")
                        
                        st.subheader(f"📍 {row['resident_username']} ({row['zone']})")
                        
                        # GAP 4 FIX: Use REAL address from DB
                        st.markdown(f"**Address:** {row['address']}")
                        
                        st.caption(f"📅 {row['date']} | 📝 Note: {row['driver_notes'] or 'None'}")

                    with c2:
                        st.write("")
                        # Task 3: Collector Inputs Weight
                        weight = st.number_input("Kg", min_value=0.1, value=2.0, key=f"w_{row['id']}")
                        
                        # COMPLETE JOB
                        if st.button("✅ LOAD", key=f"btn_load_{row['id']}", type="primary", use_container_width=True):
                            db.complete_job(row['id'], weight)
                            st.toast(f"Unit loaded: {weight}kg")
                            time.sleep(0.5)
                            st.rerun()
                            
                        # REPORT ISSUE (Use Case 9)
                        if st.button("⚠️ ISSUE", key=f"btn_fail_{row['id']}", type="secondary", use_container_width=True):
                            db.report_issue(row['id'], "Access Blocked/Contaminated")
                            st.toast("🚫 Issue Reported.")
                            time.sleep(0.5)
                            st.rerun()

    # ==========================================
    # TAB 2: LOGICAL MAP (Task 4)
    # ==========================================
    with tab2:
        st.subheader("🛰️ Satellite Navigation System")
        
        if df.empty:
            st.warning("⚠️ No active targets.")
            # Default center map (Cyberjaya)
            map_data = pd.DataFrame({'lat': [ZONE_CENTERS["Zone A"]["lat"]], 'lon': [ZONE_CENTERS["Zone A"]["lon"]]})
            st.map(map_data, zoom=13)
        else:
            st.success(f"🔵 Active Targets: {len(df)}")
            
            # GENERATE LOGICAL COORDINATES
            map_points = []
            for index, row in df.iterrows():
                # Get stable coords based on user & zone (No jumping dots)
                lat, lon = get_stable_coords(row['resident_username'], row['zone'])
                map_points.append({
                    'lat': lat,
                    'lon': lon,
                    'zone': row['zone']
                })
            
            map_data = pd.DataFrame(map_points)
            
            # Render Map
            st.map(map_data, zoom=14)
            
            # Visual Legend
            st.caption("🔴 Red Dots indicate resident pickup locations.")
            
            # AI Optimization Button (Simulation)
            if st.button("🔄 Optimize Route (AI)"):
                with st.status("Calculating optimal path...", expanded=True) as status:
                    time.sleep(0.5)
                    st.write("Grouping by Zone...")
                    time.sleep(0.5)
                    st.write("Analyzing Traffic...")
                    time.sleep(0.5)
                    status.update(label="✅ Route Optimized!", state="complete", expanded=False)
                st.success("New path loaded. Zones prioritized.")

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['username'] = "fathul"
        st.session_state['assigned_zone'] = "Zone A"
    show()