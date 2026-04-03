import streamlit as st
import json
import os

DB_FILE = "master_trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

if 'db' not in st.session_state: st.session_state.db = load_db()

st.title("🛡️ Admin Portal")

if 'a_auth' not in st.session_state:
    u = st.text_input("Admin ID")
    p = st.text_input("Password", type="password")
    if st.button("Login Admin"):
        users = st.session_state.db["users"]
        if u in users and users[u]["role"] == "admin" and users[u]["pwd"] == p:
            st.session_state.a_auth = u
            st.rerun()
        else: st.error("Invalid Admin Access")
    st.stop()

menu = st.sidebar.radio("Admin Menu", ["Create Clients", "Monitor Trades", "Settings"])

if menu == "Create Clients":
    st.header("👤 Client Management")
    c_name = st.text_input("Client Name").lower().strip()
    if st.button("✅ Add User"):
        fid = f"user_{c_name}"
        if fid not in st.session_state.db["users"]:
            st.session_state.db["users"][fid] = {"pwd": "1234", "role": "user", "bal": 0.0, "created_by": st.session_state.a_auth}
            save_db(st.session_state.db)
            st.success(f"User {fid} Added!")
        else: st.error("ID exists!")

elif menu == "Settings":
    new_p = st.text_input("New Password", type="password")
    if st.button("Update"):
        st.session_state.db["users"][st.session_state.a_auth]["pwd"] = new_p
        save_db(st.session_state.db); st.success("Updated")