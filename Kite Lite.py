import streamlit as st
import json
import os
from datetime import datetime

# --- 1. PERMANENT DATABASE ENGINE ---
DB_FILE = "master_trading_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    # Initial Master Accounts
    return {
        "users": {
            "affanwadekar": {"pwd": "1234", "role": "master", "bal": 0.0},
            "asifnagdade": {"pwd": "1234", "role": "master", "bal": 0.0}
        },
        "orders": {}, # Format: {user_id: [trade_list]}
        "ledger": {}, # Format: {user_id: [transaction_list]}
        "pnl_reports": {}
    }

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- 2. UI SETUP ---
st.set_page_config(page_title="Master Control Panel", layout="wide")

# --- 3. LOGIN SYSTEM ---
if 'logged_in_user' not in st.session_state:
    st.title("🔐 Master/Admin Login")
    u = st.text_input("Username (Master/Admin)").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Access Dashboard", use_container_width=True):
        db = st.session_state.db["users"]
        if u in db and db[u]["pwd"] == p:
            st.session_state.logged_in_user = u
            st.rerun()
        else: st.error("Access Denied: Invalid Credentials")
    st.stop()

u_id = st.session_state.logged_in_user
u_role = st.session_state.db["users"][u_id]["role"]

# --- 4. MASTER DASHBOARD (Affan & Asif) ---
if u_role == "master":
    st.sidebar.title("⭐ Master Control")
    st.sidebar.write(f"Logged in: **{u_id}**")
    
    menu = st.sidebar.radio("Master Menu", [
        "User Management", 
        "Fund Management", 
        "Live Orders & Deletion", 
        "PNL Tracker", 
        "Global Order Book",
        "Settings"
    ])

    # --- USER MANAGEMENT ---
    if menu == "User Management":
        st.header("👤 User & Admin Management")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Create New Account")
            acc_type = st.radio("Account Type", ["Admin Account", "User Account"])
            raw_name = st.text_input("Enter Name (e.g. sami, chetan)")
            
            if st.button("✅ Generate ID"):
                prefix = "admin_" if acc_type == "Admin Account" else "user_"
                full_id = f"{prefix}{raw_name.lower().replace(' ', '')}"
                
                if full_id not in st.session_state.db["users"]:
                    new_role = "admin" if acc_type == "Admin Account" else "user"
                    st.session_state.db["users"][full_id] = {"pwd": "1234", "role": new_role, "bal": 0.0, "created_by": u_id}
                    save_db(st.session_state.db)
                    st.success(f"Account Created: {full_id} | Pass: 1234")
                else: st.error("ID already exists!")

        with col2:
            st.subheader("Existing Accounts")
            all_users = list(st.session_state.db["users"].keys())
            target = st.selectbox("Select ID to Manage", [x for x in all_users if x not in ["asifnagdade", "affanwadekar"]])
            
            if st.button("Reset Password (1234)"):
                st.session_state.db["users"][target]["pwd"] = "1234"
                save_db(st.session_state.db); st.info("Password Reset")
            
            if st.button("🗑️ Permanent Delete ID"):
                del st.session_state.db["users"][target]
                save_db(st.session_state.db); st.warning("User Deleted"); st.rerun()

    # --- FUND MANAGEMENT ---
    elif menu == "Fund Management":
        st.header("💰 Fund Management (Pay-in/Out)")
        target_f = st.selectbox("Select User ID", list(st.session_state.db["users"].keys()))
        curr_bal = st.session_state.db["users"][target_f]["bal"]
        st.metric("Current Balance", f"₹{curr_bal}")
        
        amt = st.number_input("Amount (+ for Pay-in, - for Payout)", step=100.0)
        remark = st.text_input("Remark (e.g. Cash, Bank Transfer)")
        
        if st.button("Update Funds"):
            st.session_state.db["users"][target_f]["bal"] += amt
            # Record in Ledger
            if target_f not in st.session_state.db["ledger"]: st.session_state.db["ledger"][target_f] = []
            st.session_state.db["ledger"][target_f].append({
                "date": str(datetime.now()), "type": "Fund Update", "amt": amt, "remark": remark
            })
            save_db(st.session_state.db); st.success("Balance Updated!")

    # --- ORDER MANAGEMENT ---
    elif menu == "Live Orders & Deletion":
        st.header("📋 Order Management (Monitor & Delete)")
        # Logic to list all trades across users with a Delete Button for each.
        st.info("Active trades across all users will appear here. Admin can delete any 'Wrong Trade'.")

    # --- PNL TRACKER ---
    elif menu == "PNL Tracker":
        st.header("📈 All User PNL Report")
        st.write("Summary of 30% Brokerage Income for Admins & Master PNL.")

    # --- SETTINGS ---
    elif menu == "Settings":
        st.subheader("Change Master Password")
        new_p = st.text_input("New Password", type="password")
        if st.button("Update Master Password"):
            st.session_state.db["users"][u_id]["pwd"] = new_p
            save_db(st.session_state.db); st.success("Password Updated!")

    if st.sidebar.button("🚪 Logout"):
        del st.session_state.logged_in_user; st.rerun()

# --- 5. ADMIN INTERFACE (To be detailed by you later) ---
elif u_role == "admin":
    st.title(f"Admin Dashboard: {u_id}")
    st.write("Welcome Admin. You can create users and earn 30% brokerage.")
    if st.button("Logout"): del st.session_state.logged_in_user; st.rerun()
