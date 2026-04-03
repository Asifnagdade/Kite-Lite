import streamlit as st
import pandas as pd
import os

# --- MASTER LOGIN CHECK ---
if 'master_logged_in' not in st.session_state:
    st.session_state.master_logged_in = False

if not st.session_state.master_logged_in:
    st.title("🔑 Master Control Panel")
    with st.form("master_login"):
        m_id = st.text_input("Master ID")
        m_pass = st.text_input("Password", type="password")
        if st.form_submit_button("Login Master"):
            if m_id == "asifnagdade" and m_pass == "1234":
                st.session_state.master_logged_in = True
                st.rerun()
            else:
                st.error("Invalid Master ID")
else:
    # --- LOGGED IN: MASTER TABS ---
    st.title("🚀 Master Dashboard")
    
    # 1. TOP STATS (Quick View)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Funds", "₹ 5.50L")
    col2.metric("Today's PNL", "₹ +12,400", delta="2.4%")
    col3.metric("Open Orders", "5")
    col4.metric("Active Admins", "3")

    # 2. MAIN TABS (Aapke Saare Purane Features)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Funds & PNL", "📜 Order Book", "📊 Ledger", "👥 User Management", "⚙️ Password"])

    # DATABASE LOGIC
    def load_users():
        if os.path.exists("users.csv"):
            return pd.read_csv("users.csv", dtype=str)
        return pd.DataFrame([["asifnagdade", "1234", "master"]], columns=["username", "password", "role"])

    with tab1:
        st.subheader("Live Funds & Profit/Loss")
        # Dummy data for preview
        st.dataframe({
            "Client ID": ["admin_shaalan", "admin_aaliya", "test_user"],
            "Allocated Fund": ["₹ 2,00,000", "₹ 1,50,000", "₹ 50,000"],
            "Current PNL": ["₹ +4,500", "₹ -1,200", "₹ +800"]
        }, use_container_width=True)

    with tab2:
        st.subheader("Master Order Book")
        st.info("Yahan saare admins ke live orders dikhenge.")
        st.write("No active orders at the moment.")

    with tab3:
        st.subheader("Financial Ledger")
        st.write("Transaction history and settlement records.")

    with tab4:
        st.subheader("User Management")
        # Add User Form
        with st.expander("➕ Create New Admin/Partner"):
            with st.form("add_user"):
                new_name = st.text_input("Enter Partner Name")
                new_pass = st.text_input("Set Password", value="1234")
                if st.form_submit_button("Create ID"):
                    if new_name:
                        df = load_users()
                        full_id = f"admin_{new_name.lower().strip()}"
                        new_row = pd.DataFrame([[full_id, new_pass, "admin"]], columns=["username", "password", "role"])
                        pd.concat([df, new_row], ignore_index=True).to_csv("users.csv", index=False)
                        st.success(f"ID Created: {full_id}")
                        st.rerun()
        
        st.write("### Active IDs")
        st.table(load_users())

    with tab5:
        st.subheader("Change Master Password")
        st.text_input("New Master Password", type="password")
        st.button("Update Password")

    if st.sidebar.button("Logout"):
        st.session_state.master_logged_in = False
        st.rerun()
