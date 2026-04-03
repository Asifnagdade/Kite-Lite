import streamlit as st
import json
import os

DB_FILE = "master_trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {
        "users": {
            "affanwadekar": {"pwd": "1234", "role": "master", "bal": 0.0},
            "asifnagdade": {"pwd": "1234", "role": "master", "bal": 0.0}
        }
    }

def save_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

if 'db' not in st.session_state: st.session_state.db = load_db()

st.title("? Master Control Panel")

if 'm_auth' not in st.session_state:
    u = st.text_input("Master ID")
    p = st.text_input("Password", type="password")
    if st.button("Login Master"):
        if u in ["affanwadekar", "asifnagdade"] and st.session_state.db["users"][u]["pwd"] == p:
            st.session_state.m_auth = u
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

menu = st.sidebar.radio("Master Menu", ["User/Admin Management", "Fund Control", "Delete Orders"])

if menu == "User/Admin Management":
    st.header("?? Create Accounts")
    acc_type = st.radio("Account Type", ["Admin", "User"])
    name = st.text_input("Enter Name").lower().strip()
    if st.button("? Create ID"):
        prefix = "admin_" if acc_type == "Admin" else "user_"
        fid = f"{prefix}{name}"
        if fid not in st.session_state.db["users"]:
            st.session_state.db["users"][fid] = {"pwd": "1234", "role": acc_type.lower(), "bal": 0.0, "created_by": st.session_state.m_auth}
            save_db(st.session_state.db)
            st.success(f"ID Created: {fid}")
        else: st.error("ID exists!")
    
    st.divider()
    target = st.selectbox("Delete ID", [k for k in st.session_state.db["users"].keys() if k not in ["affanwadekar", "asifnagdade"]])
    if st.button("??? DELETE PERMANENTLY"):
        del st.session_state.db["users"][target]
        save_db(st.session_state.db); st.rerun()

elif menu == "Fund Control":
    st.header("?? Fund Update")
    user = st.selectbox("Select ID", list(st.session_state.db["users"].keys()))
    amt = st.number_input("Amount", step=100.0)
    if st.button("Update Balance"):
        st.session_state.db["users"][user]["bal"] += amt
        save_db(st.session_state.db); st.success("Updated!")