import streamlit as st
import json
import os
from datetime import datetime

# --- 1. PERMANENT STORAGE ENGINE ---
DB_FILE = "user_database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    # Default Admin ID
    return {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- 2. CONFIG & SYNC ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide")

# Database ko memory mein load karna
if 'user_db' not in st.session_state:
    st.session_state.user_db = load_db()
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

# --- 3. LOGIN SYSTEM ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u_in = st.text_input("Username").strip()
    p_in = st.text_input("Password", type="password").strip()
    
    if st.button("Login"):
        # Direct check from file-synced database
        db = st.session_state.user_db
        if u_in in db:
            if db[u_in]["pwd"] == p_in:
                st.session_state.logged_in_user = u_in
                st.rerun()
            else: st.error("❌ Galat Password!")
        else: st.error(f"❌ ID '{u_in}' nahi mili!")
    st.stop()

# User details
u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 4. ADMIN PANEL (FULL DELETE & PERMANENT SAVE) ---
if u_role == "admin":
    st.header("🛠️ Admin Master Control")
    t1, t2, t3 = st.tabs(["👤 ID Management", "📋 Trades Control", "💰 Ledger"])
    
    with t1:
        st.subheader("Create Permanent ID")
        new_u = st.text_input("New ID Name")
        if st.button("✅ Create and Save ID"):
            if new_u and new_u not in st.session_state.user_db:
                st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                save_db(st.session_state.user_db) # File mein save kar diya
                st.success(f"ID '{new_u}' Created! Refresh karne par bhi nahi jayegi.")
            else: st.error("ID exists or name empty.")

        st.divider()
        st.subheader("Permanent Deletion")
        m_id = st.selectbox("Select ID", [k for k in st.session_state.user_db.keys() if k != "asifnagdade"])
        if st.button("🚫 DELETE ID PERMANENTLY"):
            del st.session_state.user_db[m_id]
            save_db(st.session_state.user_db) # File se bhi delete
            st.warning("User Deleted!")
            st.rerun()

# --- 5. CLIENT SECTION ---
else:
    # First Login Password Force
    if st.session_state.user_db[u_id].get("first_login", True):
        st.title("Update Password")
        np = st.text_input("New Password", type="password")
        if st.button("Update"):
            st.session_state.user_db[u_id]["pwd"] = np
            st.session_state.user_db[u_id]["first_login"] = False
            save_db(st.session_state.user_db) # Naya password file mein save
            st.success("Updated! Please login again.")
            st.session_state.logged_in_user = None; st.rerun()
        st.stop()

    # Funds Section (Kuwait: +965 69304925)
    st.sidebar.write(f"Balance: ₹{st.session_state.user_db[u_id]['balance']}")
    if st.sidebar.button("Logout"): st.session_state.logged_in_user = None; st.rerun()
    
    st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
