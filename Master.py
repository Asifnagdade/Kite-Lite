import streamlit as st
import json
import os
from datetime import datetime

# --- DATABASE ENGINE ---
DB_FILE = "master_trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {
        "users": {
            "affanwadekar": {"pwd": "1234", "role": "master", "bal": 0.0},
            "asifnagdade": {"pwd": "1234", "role": "master", "bal": 0.0}
        },
        "orders": {}, "history": {}
    }

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

if 'db' not in st.session_state: st.session_state.db = load_db()

# --- MASTER LOGIN ---
if 'm_user' not in st.session_state:
    st.title("⭐ Master Control Panel")
    u = st.text_input("Master ID").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Login Master"):
        db = st.session_state.db["users"]
        if u in ["affanwadekar", "asifnagdade"] and db[u]["pwd"] == p:
            st.session_state.m_user = u
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- MASTER MENU ---
st.sidebar.title(f"Master: {st.session_state.m_user}")
menu = st.sidebar.radio("Master Menu", ["User Management", "Fund Management", "Delete Orders", "Settings"])

if menu == "User Management":
    st.header("👤 Create Admin or User ID")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("New Account")
        type = st.radio("Account Type", ["Admin Account", "User Account"])
        name = st.text_input("Enter Name (e.g. sami)").strip().lower()
        if st.button("✅ Create ID"):
            prefix = "admin_" if type == "Admin Account" else "user_"
            fid = f"{prefix}{name}"
            if fid not in st.session_state.db["users"]:
                st.session_state.db["users"][fid] = {"pwd": "1234", "role": type.split()[0].lower(), "bal": 0.0, "created_by": st.session_state.m_user}
                save_db(st.session_state.db); st.success(f"Created: {fid}")
            else: st.error("ID Exists!")
    with col2:
        st.subheader("Delete IDs")
        target = st.selectbox("Select ID", [k for k in st.session_state.db["users"].keys() if k not in ["affanwadekar", "asifnagdade"]])
        if st.button("🗑️ DELETE PERMANENTLY"):
            del st.session_state.db["users"][target]
            save_db(st.session_state.db); st.warning("Deleted!"); st.rerun()

elif menu == "Fund Management":
    st.header("💰 Global Wallet Control")
    user = st.selectbox("Select User/Admin", list(st.session_state.db["users"].keys()))
    amt = st.number_input("Amount (Update Balance)", step=100.0)
    if st.button("Update"):
        st.session_state.db["users"][user]["bal"] += amt
        save_db(st.session_state.db); st.success("Balance Updated!")

elif menu == "Delete Orders":
    st.header("📋 Master Order Eraser")
    st.info("Yahan se aap kisi bhi user ka galat trade permanent delete kar sakte hain.")
    # Logic for listing and popping from db["orders"]

if st.sidebar.button("Logout"): del st.session_state.m_user; st.rerun()
