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
            # Aapki fixed requirement: Affan/Asif ki ID
            if m_id == "asifnagdade" and m_pass == "1234":
                st.session_state.master_logged_in = True
                st.rerun()
            else:
                st.error("Invalid Master ID or Password")
else:
    # --- INSIDE MASTER PANEL ---
    st.title("🚀 Welcome, Master Control")
    
    if st.button("Logout"):
        st.session_state.master_logged_in = False
        st.rerun()

    st.divider()

    # --- DATABASE LOGIC ---
    def load_users():
        if os.path.exists("users.csv"):
            return pd.read_csv("users.csv", dtype=str)
        # Default data agar file nahi hai
        return pd.DataFrame([["asifnagdade", "1234", "master"]], columns=["username", "password", "role"])

    def save_user(username, password, role):
        df = load_users()
        new_user = pd.DataFrame([[username, password, role]], columns=["username", "password", "role"])
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv("users.csv", index=False)
        return df

    # --- ADD NEW ADMIN ---
    st.subheader("➕ Create New Admin/Partner")
    with st.expander("Click to Add User"):
        with st.form("add_user"):
            new_name = st.text_input("Enter Partner Name (e.g. Shaalan)")
            new_pass = st.text_input("Set Password", value="1234")
            if st.form_submit_button("Create ID"):
                if new_name:
                    full_id = f"admin_{new_name.lower().strip()}"
                    save_user(full_id, new_pass, "admin")
                    st.success(f"ID Created: {full_id}")
                    st.rerun()
                else:
                    st.error("Name is required!")

    # --- VIEW & MANAGE ---
    st.subheader("👥 Registered Users")
    df = load_users()
    st.dataframe(df, use_container_width=True)

    # Backup Button
    st.download_button("📥 Download Users Backup", df.to_csv(index=False), "users_backup.csv")
