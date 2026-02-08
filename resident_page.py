import streamlit as st
import pandas as pd
import db_manager as db
from datetime import date, timedelta
import time
import random

def calculate_level(points):
    if points is None: points = 0
    level = (points // 500) + 1
    remainder = points % 500
    progress = remainder / 500.0
    return level, progress, remainder

def get_impact_stats(df):
    if df.empty:
        return 0, 0
    completed_df = df[df['status'] == 'Completed']
    total_weight = completed_df['weight_kg'].sum()
    trees = int(total_weight / 10)
    co2 = int(total_weight * 2.5)
    return trees, co2

def show():
    username = st.session_state['username']
    current_points = db.get_user_points(username)
    history_df = db.get_resident_history(username)
    level, progress, pts_needed = calculate_level(current_points)
    trees_saved, co2_saved = get_impact_stats(history_df)
    st.markdown(f"""
        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: #2e7d32; margin:0;'>🌿 Hi, {username.capitalize()}!</h1>
            <p style='margin:0; color: #1b5e20;'>You are a <b>Level {level} Eco-Warrior</b></p>
        </div>
    """, unsafe_allow_html=True)
    col_level, col_stats = st.columns([2, 1])
    with col_level:
        st.write(f"**Level Progress:** {pts_needed}/500 pts to Lvl {level + 1}")
        st.progress(progress)
    with col_stats:
        st.write("Current Badge:")
        if level == 1:
            st.markdown("🌱 **Rookie**")
        elif level < 5:
            st.markdown("🌿 **Gatherer**")
        else:
            st.markdown("🌳 **Master of Earth**")
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Eco-Points", current_points)
    m2.metric("🌳 Trees Saved", trees_saved)
    m3.metric("☁️ CO2 Prevented", f"{co2_saved} kg")
    st.divider()
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Book & Log", "📜 History", "🎁 Rewards", "🏆 Leaderboard", "👤 Profile"])
    with tab1:
        st.subheader("♻️ Submit Recycling Log")
        if 'submission_success' not in st.session_state:
            st.session_state['submission_success'] = False
        if not st.session_state['submission_success']:
            with st.form("booking_form"):
                c1, c2 = st.columns(2)
                with c1:
                    pickup_date = st.date_input("Pickup Date", min_value=date.today(), value=date.today() + timedelta(days=1))
                with c2:
                    waste_type = st.selectbox("Waste Category", ["Recyclable (Paper/Plastic)", "E-Waste", "Bulk Item", "Garden Waste"])
                notes = st.text_area("Notes for Collector", placeholder="e.g., Box is labeled 'Glass', Gate code is 1234...")
                submitted = st.form_submit_button("🚀 Submit Log", type="primary", use_container_width=True)
                if submitted:
                    db.add_booking(username, str(pickup_date), waste_type, notes)
                    st.session_state['submission_success'] = True
                    st.rerun()
        else:
            st.success("✅ Submission Successful!")
            with st.container(border=True):
                st.markdown("### 📝 Log Details Recorded")
                st.write("Your recycling request has been logged in the system.")
                st.info("A Collector will verify the weight upon pickup to award your points.")
                if st.button("⬅️ Log Another Item"):
                    st.session_state['submission_success'] = False
                    st.rerun()
    with tab2:
        if history_df.empty:
            st.info("🤷‍♂️ No missions yet. Start recycling to earn badges!")
        else:
            display_df = history_df.rename(columns={
                'date': 'Date',
                'waste_type': 'Category',
                'status': 'Status',
                'weight_kg': 'Weight (kg)'
            })
            display_df['Weight (kg)'] = display_df.apply(
                lambda x: f"{x['Weight (kg)']}" if x['Status'] == 'Completed' else "TBD", axis=1
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    with tab3:
        st.subheader("🎁 Rewards Catalog")
        items_df = db.get_rewards_list()
        if items_df.empty:
            st.warning("Rewards catalog is currently empty. Check back later!")
        else:
            for index, row in items_df.iterrows():
                with st.container(border=True):
                    c_img, c_txt, c_btn = st.columns([1, 3, 1])
                    with c_img:
                        icon = "🎫"
                        name = row['item_name'].lower()
                        if "food" in name: icon = "🍔"
                        elif "straw" in name: icon = "🥤"
                        elif "shirt" in name: icon = "👕"
                        elif "netflix" in name: icon = "🎬"
                        elif "cinema" in name: icon = "🍿"
                        st.markdown(f"# {icon}")
                    with c_txt:
                        st.write(f"**{row['item_name']}**")
                        st.caption(f"Cost: {row['cost_points']} pts | Stock: {row['stock_level']}")
                    with c_btn:
                        can_afford = current_points >= row['cost_points']
                        has_stock = row['stock_level'] > 0
                        btn_key = f"redeem_{row['id']}"
                        if st.button("Claim", key=btn_key, disabled=not (can_afford and has_stock), type="primary" if can_afford else "secondary"):
                            success, msg = db.redeem_item(username, row['item_name'], row['cost_points'])
                            if success:
                                st.balloons()
                                st.success(f"Redeemed! Code: {msg}")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(msg)
    with tab4:
        st.subheader("🏆 Cyberjaya Top Recyclers")
        st.caption("Real-time ranking of all residents in the system.")
        all_users = db.get_all_users()
        resident_ranks = all_users[all_users['role'] == 'Resident'].copy()
        if resident_ranks.empty:
            st.info("No residents found in the leaderboard.")
        else:
            resident_ranks = resident_ranks.sort_values(by='current_points', ascending=False)
            resident_ranks['Rank'] = range(1, len(resident_ranks) + 1)
            def get_rank_icon(rank):
                if rank == 1: return "🥇"
                if rank == 2: return "🥈"
                if rank == 3: return "🥉"
                return str(rank)
            resident_ranks['Rank'] = resident_ranks['Rank'].apply(get_rank_icon)
            leaderboard_display = resident_ranks[['Rank', 'username', 'current_points', 'resident_zone']].rename(columns={
                'username': 'Resident',
                'current_points': 'Total Points',
                'resident_zone': 'Zone'
            })
            st.dataframe(
                leaderboard_display,
                use_container_width=True,
                hide_index=True
            )
    with tab5:
        st.subheader("👤 My Profile")
        details = db.get_resident_details(username)
        if details:
            full_name = details['full_name'] or ""
            address = details['address'] or ""
            zone = details['zone'] or "Unassigned"
            with st.form("edit_profile_form"):
                st.markdown("#### 📝 Edit Personal Details")
                new_name = st.text_input("Full Name", value=full_name)
                new_address = st.text_input("Address", value=address)
                st.caption(f"Current Zone: {zone} (Contact Admin to change)")
                if st.form_submit_button("💾 Save Changes"):
                    if db.update_resident_profile(username, new_name, new_address):
                        st.success("Profile updated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update profile.")
            st.divider()
            with st.form("change_pass_form"):
                st.markdown("#### 🔒 Security")
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm New Password", type="password")
                if st.form_submit_button("🔑 Update Password"):
                    if new_pass and new_pass == confirm_pass:
                        if len(new_pass) > 0:
                            if db.update_password(username, new_pass):
                                st.success("Password changed! Please login again.")
                                time.sleep(2)
                                st.session_state['logged_in'] = False
                                st.rerun()
                            else:
                                st.error("Error updating password.")
                        else:
                            st.error("Password cannot be empty.")
                    else:
                        st.error("Passwords do not match.")
        else:
            st.error("Could not load profile data.")

if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['username'] = "john"
        st.session_state['role'] = "Resident"
    show()