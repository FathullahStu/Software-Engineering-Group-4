# FILE: admin_page.py
# Written by: Group 4 (Afiq & Min)
# Purpose: Admin Command Center with Team Zone Management (Use Case 11).

import streamlit as st
import pandas as pd
import db_manager as db
import time

def show():
    # 1. GET CONTEXT
    username = st.session_state.get('username', 'Admin')
    
    # HERO SECTION
    st.markdown(f"""
        <div style='background-color: #1565C0; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='margin:0; color: white; font-family: sans-serif;'>🛡️ ADMIN COMMAND CENTER</h2>
            <p style='margin:0; opacity: 0.8;'><b>Officer:</b> {username.upper()} | <b>Security Level:</b> ALPHA | <b>Server:</b> 🟢 ONLINE</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. KEY METRICS
    all_users = db.get_all_users()
    all_bookings = db.get_all_bookings_admin()
    
    total_users = len(all_users)
    if not all_bookings.empty:
        total_waste = all_bookings[all_bookings['status'] == 'Completed']['weight_kg'].sum()
        pending_count = len(all_bookings[all_bookings['status'] == 'Pending'])
    else:
        total_waste = 0.0
        pending_count = 0
    
    c1, c2, c3 = st.columns(3)
    with c1: st.info(f"👥 **Users Active**\n# {total_users}")
    with c2: st.success(f"♻️ **Total Recycled**\n# {total_waste} kg")
    with c3: st.warning(f"⏳ **Pending Jobs**\n# {pending_count}")
    
    st.divider()

    # 3. MAIN TABS
    tab1, tab2, tab3 = st.tabs(["📊 Analytics", "👮 User Database", "👥 Team & Zones"])
    
    # --- TAB 1: ANALYTICS ---
    with tab1:
        st.subheader("📡 Live Data Feed")
        if not all_bookings.empty:
            col_chart, col_log = st.columns([2, 1])
            with col_chart:
                st.markdown("#### 📉 Waste Composition")
                st.bar_chart(all_bookings['waste_type'].value_counts(), color="#1565C0")
            with col_log:
                st.markdown("#### 📝 Activity Log")
                st.dataframe(all_bookings[['waste_type', 'status']].tail(8), use_container_width=True, hide_index=True)
            
            # Export
            csv = all_bookings.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Mission Report (CSV)", csv, "ecosort_report.csv", "text/csv")
        else:
            st.info("System Standby. Waiting for incoming data streams.")

    # --- TAB 2: USER DB ---
    with tab2:
        st.subheader("📂 Registered Personnel")
        search = st.text_input("🔍 Search Database", placeholder="Enter Name...")
        
        # Filter
        filtered = all_users
        if search:
            filtered = all_users[all_users['username'].str.contains(search, case=False, na=False)]
            
        # Split Data
        residents = filtered[filtered['role'] == 'Resident']
        staff = filtered[filtered['role'] != 'Resident']
        
        c_res, c_staff = st.columns(2)
        
        with c_res:
            st.markdown("### 🏠 Residents")
            st.dataframe(residents[['username', 'current_points', 'resident_zone']], hide_index=True, use_container_width=True)

        with c_staff:
            st.markdown("### 💼 Staff")
            st.dataframe(staff[['username', 'role', 'assigned_zone']], hide_index=True, use_container_width=True)

    # --- TAB 3: TEAM & ZONES (New for Gap 3) ---
    with tab3:
        st.subheader("🗺️ Operational Assignments")
        st.caption("Assign Collectors to specific zones (Use Case 11).")
        
        # 1. Assignment Form
        with st.form("assign_zone_form"):
            col_s1, col_s2 = st.columns(2)
            
            # Get list of Collectors
            collectors = all_users[all_users['role'] == 'Collector']['username'].tolist()
            
            with col_s1:
                selected_driver = st.selectbox("Select Officer", collectors)
            with col_s2:
                selected_zone = st.selectbox("Assign Zone", ["Zone A", "Zone B", "Zone C", "Zone D"])
            
            if st.form_submit_button("✅ Update Assignment"):
                success = db.update_employee_zone(selected_driver, selected_zone)
                if success:
                    st.success(f"Officer {selected_driver} reassigned to {selected_zone}.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Update failed.")
        
        # 2. Current Status Table
        st.divider()
        st.markdown("#### 📋 Current Duty Roster")
        roster = all_users[all_users['role'] == 'Collector'][['username', 'assigned_zone', 'role']]
        st.dataframe(roster, use_container_width=True, hide_index=True)

    # --- DANGER ZONE ---
    with st.expander("🔴 NUCLEAR OPTION (Reset Data)"):
        if st.button("☢️ FLUSH DATABASE"):
            conn = db.create_connection()
            conn.cursor().execute("DELETE FROM pickup_requests")
            conn.commit()
            conn.close()
            st.warning("Database flushed.")
            time.sleep(1)
            st.rerun()

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['username'] = "afiq"
    show()