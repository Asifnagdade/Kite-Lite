import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide")

# --- 2. GLOBAL DATA INITIALIZATION ---
# Isse data reset nahi hoga refresh par
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 3. LOGIN ENGINE (STRICT CHECK) ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u_input = st.text_input("Username")
    p_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Direct check from session state for real-time updates
        if u_input in st.session_state.user_db:
            correct_pwd = st.session_state.user_db[u_input]["pwd"]
            if p_input == correct_pwd:
                st.session_state.logged_in_user = u_input
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Wrong Password!")
        else:
            st.error("User Not Found!")
    st.stop()

# Current User Data
curr_u = st.session_state.logged_in_user
curr_role = st.session_state.user_db[curr_u]["role"]

# --- 4. ADMIN PANEL (WITH PERMANENT DELETE) ---
if curr_role == "admin":
    st.header("🛠️ Admin Master Control")
    t1, t2, t3, t4 = st.tabs(["👤 User Mgmt", "💰 Ledger", "📋 Live Trades", "📑 Trade History"])
    
    with t1:
        # Create User
        st.subheader("Create New ID")
        new_id = st.text_input("New Username")
        if st.button("Create"):
            st.session_state.user_db[new_id] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
            st.success(f"ID {new_id} created with Password: 1234")
        
        st.divider()
        # Reset & Delete
        st.subheader("Manage Existing IDs")
        manage_id = st.selectbox("Select User", [k for k in st.session_state.user_db.keys() if k != "asifnagdade"])
        if st.button("Reset Password to 1234"):
            st.session_state.user_db[manage_id]["pwd"] = "1234"
            st.session_state.user_db[manage_id]["first_login"] = True
            st.success(f"Password for {manage_id} is now 1234")
        
        if st.button("🗑️ DELETE THIS USER PERMANENTLY"):
            del st.session_state.user_db[manage_id]
            st.warning("User Deleted!")
            st.rerun()

    with t3: # Live Positions Deletion
        st.subheader("Live Portfolio Control")
        if st.session_state.portfolio:
            for i, p in enumerate(st.session_state.portfolio):
                col1, col2 = st.columns([4, 1])
                col1.write(f"User: {p['User']} | {p['Sym']} | Qty: {p['Qty']}")
                if col2.button(f"Delete Trade {i}", key=f"p_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()
        else: st.info("No Live Trades")

    with t4: # Permanent History Deletion
        st.subheader("Permanent Record Deletion")
        if st.session_state.order_history:
            for i, h in enumerate(st.session_state.order_history):
                col1, col2 = st.columns([4, 1])
                col1.write(f"{h['User']} | {h['Sym']} | {h['Time']}")
                if col2.button(f"🗑️ Delete History {i}", key=f"h_{i}"):
                    st.session_state.order_history.pop(i)
                    st.rerun()

# --- 5. CLIENT SECTION ---
else:
    # First Login Password Change
    if st.session_state.user_db[curr_u].get("first_login", True):
        st.title("Set Your Password")
        new_p = st.text_input("New Password", type="password")
        if st.button("Save"):
            st.session_state.user_db[curr_u]["pwd"] = new_p
            st.session_state.user_db[curr_u]["first_login"] = False
            st.success("Password Updated!")
            st.rerun()
        st.stop()

    # Funds Section with WhatsApp
    st.sidebar.write(f"Balance: ₹{st.session_state.user_db[curr_u]['balance']}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

    st.subheader("Funds")
    st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
    f_amt = st.number_input("Amount", step=100)
    wa_link = f"https://wa.me/96569304925?text=Payin%20Request%20{f_amt}%20User%20{curr_u}"
    if st.button("Pay-in via WhatsApp"):
        st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_link}">', unsafe_allow_html=True)
