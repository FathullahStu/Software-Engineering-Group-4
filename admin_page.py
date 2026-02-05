# FILE: admin_page.py
# Written by: Group 4 (Afiq & Min)
# Purpose: Visually Enhanced Admin Command Center.

import streamlit as st
import pandas as pd
import db_manager as db
import time

def show():
    """
    The Main Admin Dashboard.
    """
    # 1. GET ADMIN CONTEXT
    username = st.session_state.get('username', 'Admin')
    
    # ==========================================
    # 🎨 HERO SECTION (Command Center Style)
    # ==========================================
    # We use Royal Blue for that "Authority/System" feel
    st.markdown(f"""
        <div style='background-color: #1565C0; padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='margin:0; color: white; font-family: sans-serif;'>🛡️ ADMIN COMMAND CENTER</h2>
            <p style='margin:0; opacity: 0.8;'><b>Officer:</b> {username.upper()} | <b>Security Level:</b> ALPHA | <b>Server:</b> 🟢 ONLINE</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. KEY METRICS (With Visual Pop)
    all_users = db.get_all_users()
    all_bookings = db.get_all_bookings_admin()
    
    # Calculate Stats
    total_users = len(all_users)
    if not all_bookings.empty:
        total_waste = all_bookings[all_bookings['status'] == 'Completed']['weight_kg'].sum()
        pending_count = len(all_bookings[all_bookings['status'] == 'Pending'])
    else:
        total_waste = 0.0
        pending_count = 0
    
    # Custom colored metric containers
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"👥 **Users Active**\n# {total_users}")
    with c2:
        st.success(f"♻️ **Total Recycled**\n# {total_waste} kg")
    with c3:
        st.warning(f"⏳ **Pending Jobs**\n# {pending_count}")
    
    st.divider()

    # 3. MAIN TABS
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "👮 User Database"])
    
    # ==========================================
    # TAB 1: ANALYTICS
    # ==========================================
    with tab1:
        st.subheader("📡 Live Data Feed")
        
        if not all_bookings.empty:
            col_chart, col_log = st.columns([2, 1])
            
            with col_chart:
                st.markdown("#### 📉 Waste Composition")
                # Count waste types
                waste_counts = all_bookings['waste_type'].value_counts()
                st.bar_chart(waste_counts, color="#1565C0") # Blue bars
                
            with col_log:
                st.markdown("#### 📝 Activity Log")
                # Show last 8 entries
                st.dataframe(
                    all_bookings[['waste_type', 'status']].tail(8),
                    use_container_width=True, 
                    hide_index=True
                )
            
            # --- DOWNLOAD BUTTON (Reporting Feature) ---
            st.write("")
            st.markdown("#### 📥 System Reporting")
            
            # Convert DF to CSV
            csv = all_bookings.to_csv(index=False).encode('utf-8')
            
            col_dl, col_spacer = st.columns([1, 2])
            with col_dl:
                st.download_button(
                    label="Export Mission Report (CSV)",
                    data=csv,
                    file_name="ecosort_mission_report.csv",
                    mime="text/csv",
                    type="primary",
                    help="Download full database record for offline analysis."
                )
                
        else:
            st.info("System Standby. Waiting for incoming data streams from Residents.")

    # ==========================================
    # TAB 2: USER DB (Clean & Separated)
    # ==========================================
    with tab2:
        st.subheader("📂 Registered Personnel")
        
        search_query = st.text_input("🔍 Search Database", placeholder="Enter ID or Name...")
        
        # Filter Logic
        if search_query:
            filtered_users = all_users[all_users['username'].str.contains(search_query, case=False, na=False)]
        else:
            filtered_users = all_users
            
        # Split Residents vs Staff (So we don't show confusing 0 points for admins)
        residents_df = filtered_users[filtered_users['role'] == 'Resident']
        staff_df = filtered_users[filtered_users['role'] != 'Resident']
        
        col_res, col_staff = st.columns(2)
        
        # 1. RESIDENTS TABLE (Shows Points)
        with col_res:
            st.markdown("### 🏠 Civilians (Residents)")
            if not residents_df.empty:
                display_res = residents_df[['username', 'points']].copy()
                st.dataframe(
                    display_res, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "points": st.column_config.ProgressColumn(
                            "Eco-Points",
                            format="%d pts",
                            min_value=0,
                            max_value=1000,
                        )
                    }
                )
            else:
                st.caption("No records found.")

        # 2. STAFF TABLE (Shows Role, Hides Points)
        with col_staff:
            st.markdown("### 💼 Staff (Admin/Collector)")
            if not staff_df.empty:
                display_staff = staff_df[['username', 'role']].copy()
                st.dataframe(
                    display_staff, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "role": st.column_config.TextColumn("Clearance Level")
                    }
                )
            else:
                st.caption("No records found.")
        
        st.divider()
        
        # DANGER ZONE (Reset Button)
        with st.expander("🔴 NUCLEAR OPTION (Reset Data)"):
            st.error("WARNING: This action is irreversible. It will wipe all booking history.")
            if st.button("☢️ FLUSH DATABASE"):
                conn = db.create_connection()
                c = conn.cursor()
                c.execute("DELETE FROM bookings")
                conn.commit()
                conn.close()
                st.toast("💥 Database flushed. System Clean.")
                time.sleep(1)
                st.rerun()

# ==========================================
# TEST BLOCK (For Afiq/Min Isolation Test)
# ==========================================
if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['username'] = "afiq"
        st.session_state['role'] = "Admin"

    with st.sidebar:
        st.header("Admin Mode")
        st.write("User: Afiq")
        
    show()