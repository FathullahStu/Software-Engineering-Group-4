# FILE: resident_page.py
# Written by: Group 4 (Amir)
# Purpose: Gamified Resident Dashboard.

import streamlit as st
import pandas as pd
import db_manager as db
from datetime import date, timedelta
import time
import random

def calculate_level(points):
    """
    RPG Logic: Returns current level and progress to next level.
    Each level requires 500 points.
    """
    level = (points // 500) + 1
    remainder = points % 500
    progress = remainder / 500.0
    return level, progress, remainder

def get_impact_stats(df):
    """
    Converts trash weight into 'fun' stats.
    """
    if df.empty:
        return 0, 0
    total_weight = df[df['status'] == 'Completed']['weight_kg'].sum()
    
    # Fake science for gamification:
    # 10kg waste = 1 Tree Saved
    # 1kg waste = 2.5kg CO2 prevented
    trees = int(total_weight / 10)
    co2 = int(total_weight * 2.5)
    
    return trees, co2

def show():
    """
    The Gamified Resident Dashboard.
    """
    # 1. GET USER CONTEXT
    username = st.session_state['username']
    
    # Fetch Data
    current_points = db.get_user_points(username)
    history_df = db.get_resident_history(username)
    
    # Calculate Gamification Stats
    level, progress, pts_needed = calculate_level(current_points)
    trees_saved, co2_saved = get_impact_stats(history_df)
    
    # ==========================================
    # 🌟 HERO SECTION (The "Lighten Up" Part)
    # ==========================================
    # We use a container with a background color effect (using Markdown hack)
    st.markdown(f"""
        <div style='background-color: #e8f5e9; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: #2e7d32; margin:0;'>🌿 Hi, {username.capitalize()}!</h1>
            <p style='margin:0; color: #1b5e20;'>You are a <b>Level {level} Eco-Warrior</b></p>
        </div>
    """, unsafe_allow_html=True)

    # LEVEL PROGRESS BAR
    col_level, col_stats = st.columns([2, 1])
    
    with col_level:
        st.write(f"**Level Progress:** {pts_needed}/500 pts to Lvl {level + 1}")
        st.progress(progress)
        if progress > 0.9:
            st.caption("🔥 You are so close to leveling up!")
            
    with col_stats:
        # Mini Badges Row
        st.write("Current Badge:")
        if level == 1:
            st.markdown("🌱 **Rookie**")
        elif level < 5:
            st.markdown("🌿 **Gatherer**")
        else:
            st.markdown("🌳 **Master of Earth**")

    # IMPACT METRICS (Gamified Stats)
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Eco-Points", current_points, delta="Spend these!")
    m2.metric("🌳 Trees Saved", trees_saved, help="Approximate impact based on recycled weight.")
    m3.metric("☁️ CO2 Prevented", f"{co2_saved} kg", help="Carbon emissions prevented.")
    
    st.divider()

    # ==========================================
    # MAIN TABS
    # ==========================================
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Book Pickup", "📜 History", "🎁 Shop", "🏆 Leaderboard"])
    
    # --- TAB 1: BOOKING (With Fun Feedback) ---
    with tab1:
        st.subheader("♻️ Recycle Something New")
        with st.form("booking_form"):
            c1, c2 = st.columns(2)
            with c1:
                pickup_date = st.date_input("When?", min_value=date.today(), value=date.today() + timedelta(days=1))
            with c2:
                waste_type = st.selectbox("What?", ["Recyclable", "E-Waste", "Bulk Item", "Garden Waste"])
            
            notes = st.text_area("Notes", placeholder="Gate code, specific location, etc.")
            
            # Big Green Button
            submitted = st.form_submit_button("🚀 Launch Mission", type="primary", use_container_width=True)
            
            if submitted:
                db.add_booking(username, str(pickup_date), waste_type)
                
                # GAMIFICATION: BALLOONS!
                st.balloons() 
                st.success("✅ Mission Confirmed! Team EcoSort is on the way.")
                time.sleep(1.5)
                st.rerun()

    # --- TAB 2: HISTORY ---
    with tab2:
        if history_df.empty:
            st.info("🤷‍♂️ No missions yet. Start recycling to earn badges!")
        else:
            st.dataframe(
                history_df[['date', 'waste_type', 'status', 'weight_kg']],
                use_container_width=True,
                hide_index=True
            )

    # --- TAB 3: REWARDS (Visual Upgrade) ---
    with tab3:
        st.subheader("🎁 Loot Box / Rewards")
        items_df = db.get_rewards_list()
        
        for index, row in items_df.iterrows():
            with st.container(border=True):
                c_img, c_txt, c_btn = st.columns([1, 3, 1])
                
                with c_img:
                    # Fun Emojis based on item name
                    icon = "🎫"
                    if "Food" in row['item_name']: icon = "🍔"
                    elif "Straw" in row['item_name']: icon = "🥤"
                    elif "Shirt" in row['item_name']: icon = "👕"
                    elif "Netflix" in row['item_name']: icon = "🎬"
                    st.markdown(f"# {icon}")
                    
                with c_txt:
                    st.write(f"**{row['item_name']}**")
                    st.caption(f"Cost: {row['cost']} pts")
                    
                with c_btn:
                    can_afford = current_points >= row['cost']
                    if st.button("Claim", key=f"r_{row['id']}", disabled=not can_afford, type="primary" if can_afford else "secondary"):
                        success, msg = db.redeem_item(username, row['item_name'], row['cost'])
                        if success:
                            st.snow() # DIFFERENT ANIMATION FOR REWARDS
                            st.success(f"Code: {msg}")
                        else:
                            st.error(msg)

    # --- TAB 4: LEADERBOARD (Social Competition) ---
    with tab4:
        st.subheader("🏆 Cyberjaya Top Recyclers")
        st.caption("Compete with your neighbors to save the planet!")
        
        # Fake Data for the "Community Feeling"
        leaderboard_data = [
            {"Rank": "🥇", "User": "Sarah_99", "Points": 2450, "Level": "5"},
            {"Rank": "🥈", "User": "Eco_Mike", "Points": 2100, "Level": "5"},
            {"Rank": "🥉", "User": "Green_Lee", "Points": 1850, "Level": "4"},
            {"Rank": "4", "User": "You", "Points": current_points, "Level": str(level)},
            {"Rank": "5", "User": "Tan_Ah_Beng", "Points": 800, "Level": "2"},
        ]
        st.table(leaderboard_data)

# ==========================================
# TEST BLOCK
# ==========================================
if __name__ == "__main__":
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = True
        st.session_state['username'] = "john"
        st.session_state['role'] = "Resident"
    show()