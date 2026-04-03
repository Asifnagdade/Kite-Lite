import streamlit as st
import json
import os
import pandas as pd # Tables dikhane ke liye zaroori hai
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
        "orders": {}, # For history
        "positions": {} # For RUNNING trades
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
        db_users = st.session_state.db["users"]
        if u in ["affanwadekar", "asifnagdade"] and db_users[u]["pwd"] == p:
            st.session_state.m_user = u
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- MASTER MENU ---
st.sidebar.title(f"Master: {st.session_state.m_user}")
menu = st.sidebar.radio("Master Menu", ["User Management", "Live Monitoring (PNL)", "Fund Management", "Delete Orders"])

# --- 1. USER MANAGEMENT (Same as before) ---
if menu == "User Management":
    st.header("👤 Create Admin or User ID")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("New Account")
        type_acc = st.radio("Account Type", ["Admin Account", "User Account"])
        name = st.text_input("Enter Name (e.g. sami)").strip().lower()
        if st.button("✅ Create ID"):
            prefix = "admin_" if type_acc == "Admin Account" else "user_"
            fid = f"{prefix}{name}"
            if fid not in st.session_state.db["users"]:
                st.session_state.db["users"][fid] = {"pwd": "1234", "role": type_acc.split()[0].lower(), "bal": 0.0, "created_by": st.session_state.m_user}
                save_db(st.session_state.db); st.success(f"Created: {fid}")
            else: st.error("ID Exists!")
    with col2:
        st.subheader("Delete IDs")
        target = st.selectbox("Select ID", [k for k in st.session_state.db["users"].keys() if k not in ["affanwadekar", "asifnagdade"]])
        if st.button("🗑️ DELETE PERMANENTLY"):
            del st.session_state.db["users"][target]
            save_db(st.session_state.db); st.warning("Deleted!"); st.rerun()

# --- 2. LIVE MONITORING & PNL (NEW SECTION) ---
elif menu == "Live Monitoring (PNL)":
    st.header("📈 Users Live Status & PNL")
    
    # User Selection to see details
    all_users = [k for k, v in st.session_state.db["users"].items() if v["role"] == "user"]
    
    if not all_users:
        st.info("Abhi koi users nahi hain.")
    else:
        for user in all_users:
            with st.expander(f"📊 Status: {user.upper()}"):
                c1, c2, c3 = st.columns(3)
                # User Balance
                bal = st.session_state.db["users"][user]["bal"]
                c1.metric("Wallet Balance", f"₹{bal}")
                
                # PNL Calculation (Dummy calculation based on open positions)
                # Yahan hum positions se data uthayenge jab user trade lega
                user_positions = st.session_state.db.get("positions", {}).get(user, [])
                
                if user_positions:
                    st.subheader("Running Trades")
                    df = pd.DataFrame(user_positions)
                    st.dataframe(df, use_container_width=True)
                    
                    # Total PNL (Isme logic user ke live price vs buy price ka aayega)
                    total_pnl = 500.0  # Example value
                    c2.metric("Running PNL", f"₹{total_pnl}", delta_color="normal")
                else:
                    st.write("Is user ka koi running trade nahi hai.")
                    c2.metric("Running PNL", "₹0.00")

# --- 3. FUND MANAGEMENT ---
elif menu == "Fund Management":
    st.header("💰 Global Wallet Control")
    user = st.selectbox("Select User/Admin", list(st.session_state.db["users"].keys()))
    amt = st.number_input("Amount (Update Balance)", step=100.0)
    if st.button("Update"):
        st.session_state.db["users"][user]["bal"] += amt
        save_db(st.session_state.db); st.success(f"Updated! New Balance: ₹{st.session_state.db['users'][user]['bal']}")

# --- 4. DELETE ORDERS ---
elif menu == "Delete Orders":
    st.header("📋 Master Order Eraser")
    st.warning("Master can delete orders from history here.")
    # Display Order History with Delete Button
    all_orders = st.session_state.db.get("orders", {})
    if not all_orders:
        st.info("No orders found in database.")
    else:
        for u_id, orders in all_orders.items():
            st.subheader(f"Orders for {u_id}")
            for idx, order in enumerate(orders):
                col1, col2 = st.columns([4, 1])
                col1.write(f"{order['symbol']} | {order['type']} | Qty: {order['qty']} | Price: {order['price']}")
                if col2.button(f"🗑️ Delete", key=f"del_{u_id}_{idx}"):
                    st.session_state.db["orders"][u_id].pop(idx)
                    save_db(st.session_state.db)
                    st.rerun()

if st.sidebar.button("Logout"): del st.session_state.m_user; st.rerun()
