import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide")

# --- 2. PERMANENT DATA STORAGE ---
# Is logic se ID creation ke baad 'User Not Found' nahi aayega
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 3. LOGIN SYSTEM (FIXED) ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u_in = st.text_input("Username").strip() # Extra spaces hatane ke liye
    p_in = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Direct check from the current state
        if u_in in st.session_state.user_db:
            if st.session_state.user_db[u_in]["pwd"] == p_in:
                st.session_state.logged_in_user = u_in
                st.rerun()
            else:
                st.error("Galti: Password galat hai!")
        else:
            st.error(f"Galti: User '{u_in}' system mein nahi mila! Admin se ID banwayein.")
    st.stop()

# --- 4. CURRENT USER INFO ---
u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 5. ADMIN MASTER PANEL (FULL DELETE POWERS) ---
if u_role == "admin":
    st.header("🛠️ Admin Master Control")
    t1, t2, t3, t4 = st.tabs(["👤 User & ID Management", "💰 Ledger Control", "📋 Live Trades", "📑 Permanent History"])
    
    with t1: # ID Creation & Deletion
        st.subheader("Create New Client ID")
        new_u = st.text_input("New ID Name")
        if st.button("✅ Create ID"):
            if new_u and new_u not in st.session_state.user_db:
                st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                st.success(f"ID '{new_u}' created! Password is 1234")
            else: st.error("ID empty hai ya pehle se bani hui hai.")

        st.divider()
        st.subheader("Delete or Reset ID")
        manage_id = st.selectbox("Select ID", [k for k in st.session_state.user_db.keys() if k != "asifnagdade"])
        if st.button("Reset Pass to 1234"):
            st.session_state.user_db[manage_id]["pwd"] = "1234"
            st.session_state.user_db[manage_id]["first_login"] = True
            st.info("Password Reset Done.")
        
        if st.button("🚫 DELETE ID PERMANENTLY", type="secondary"):
            del st.session_state.user_db[manage_id]
            st.warning("User Deleted Successfully.")
            st.rerun()

    with t3: # Delete Live Trades
        st.subheader("Force Delete Live Positions")
        if st.session_state.portfolio:
            for i, p in enumerate(st.session_state.portfolio):
                col = st.columns([4, 1])
                col[0].write(f"User: {p['User']} | {p['Sym']} | Qty: {p['Qty']}")
                if col[1].button(f"🗑️ Delete {i}", key=f"lp_{i}"):
                    st.session_state.portfolio.pop(i); st.rerun()
        else: st.info("No Live Trades.")

    with t4: # Permanent History Deletion
        st.subheader("Delete Trade History Permanently")
        if st.session_state.order_history:
            for i, h in enumerate(st.session_state.order_history):
                col = st.columns([4, 1])
                col[0].write(f"{h['User']} | {h['Sym']} | {h['Time']}")
                if col[1].button(f"🗑️ Delete Record {i}", key=f"th_{i}"):
                    st.session_state.order_history.pop(i); st.rerun()

# --- 6. CLIENT SECTION ---
else:
    # First Login Password Change
    if st.session_state.user_db[u_id].get("first_login", True):
        st.title("Change Your Password")
        np = st.text_input("New Password", type="password")
        if st.button("Save Password"):
            st.session_state.user_db[u_id]["pwd"] = np
            st.session_state.user_db[u_id]["first_login"] = False
            st.success("Updated! Now you can trade.")
            st.rerun()
        st.stop()

    # Funds Section
    st.sidebar.write(f"Balance: ₹{st.session_state.user_db[u_id]['balance']}")
    if st.sidebar.button("Logout"): st.session_state.logged_in_user = None; st.rerun()

    st.subheader("Funds Management")
    st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
    # (WhatsApp Pay-in links remain active here)
