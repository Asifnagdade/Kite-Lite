import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import random

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- 2. MASTER DATA ---
MASTER_DATA = {
    "NSE": {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "SBIN": "SBIN.NS"},
    "MCX": {
        "GOLD": "GC=F", "SILVER": "SI=F", "COPPER": "HG=F", "CRUDEOIL": "CL=F",
        "GOLDM": "GOLDM.NS", "NATURALGAS": "NG=F", "ZINC": "ZINC1!S",
        "SILVERM": "SIL=F", "SILVERMIC": "SILMIC.NS", "CRUDEOILM": "QM=F",
        "ZINCMINI": "ZINC-MINI.NS", "NATGASMINI": "QG=F"
    }
}

# --- 3. SESSION STATE ---
if 'user_db' not in st.session_state:
    # Admin details preserved
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'watchlists' not in st.session_state: st.session_state.watchlists = {"NSE": ["NIFTY 50"], "MCX": ["CRUDEOILM"]}
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 4. LOGIN SYSTEM ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u
            st.rerun()
        else:
            st.error("Invalid Username or Password")
    st.stop()

u_id = st.session_state.logged_in_user
# Force refresh user data from DB
u_role = st.session_state.user_db[u_id]["role"]

# --- 5. COMPULSORY PASSWORD CHANGE FOR NEW/RESET USERS ---
if st.session_state.user_db[u_id].get("first_login", True) and u_role == "user":
    st.warning("👋 Welcome! Since this is your first login or your password was reset, please set a new password.")
    new_p = st.text_input("Set New Password", type="password")
    conf_p = st.text_input("Confirm New Password", type="password")
    if st.button("Update and Continue"):
        if new_p == conf_p and len(new_p) > 3:
            st.session_state.user_db[u_id]["pwd"] = new_p
            st.session_state.user_db[u_id]["first_login"] = False
            st.success("Password Updated! Refreshing...")
            st.rerun()
        else:
            st.error("Passwords do not match or are too short.")
    st.stop()

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{u_id.upper()}**")
    if u_role == "user":
        st.metric("Margin Available", f"₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()

# --- 7. MAIN INTERFACE ---
if u_role == "admin":
    st.header("🛠️ Admin Master Panel")
    t1, t2, t3, t4 = st.tabs(["👤 Client Management", "💰 Ledger Control", "📋 Live Monitor", "📑 Trade History"])
    
    with t1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Add New Client")
            new_u = st.text_input("Username", key="new_u")
            if st.button("Create User"):
                if new_u not in st.session_state.user_db:
                    # New user starts with 0 funds and must change password
                    st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                    st.success(f"User {new_u} created with default pass '1234'")
                else: st.error("User exists.")
        
        with col2:
            st.subheader("Reset Client Password")
            reset_u = st.selectbox("Select Client", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
            if st.button("Reset to 1234"):
                st.session_state.user_db[reset_u]["pwd"] = "1234"
                # Resetting first_login forces user to change it on next login
                st.session_state.user_db[reset_u]["first_login"] = True 
                st.success(f"Password for {reset_u} reset to 1234. They must change it on login.")

    with t2:
        st.subheader("Ledger Management")
        target = st.selectbox("Select Account", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (+ Payin / - Payout)")
        rem = st.text_input("Remark")
        if st.button("Apply to Ledger"):
            st.session_state.user_db[target]["balance"] += amt
            st.session_state.user_db[target]["ledger"].append({"Date": datetime.now(), "Amt": amt, "Remark": rem, "Bal": st.session_state.user_db[target]["balance"]})
            st.success("Balance Updated.")

    with t3:
        st.subheader("Real-Time Monitor (All Users)")
        if st.session_state.portfolio: st.table(pd.DataFrame(st.session_state.portfolio))
        else: st.info("No open positions.")

    with t4:
        st.subheader("System Trade Audit")
        if st.session_state.order_history: st.table(pd.DataFrame(st.session_state.order_history))
        else: st.info("No history.")

else:
    # CLIENT TRADING INTERFACE
    st.info(f"Welcome {u_id}. Start trading in Terminal or check your Funds.")
    # (Client Watchlist, Terminal, Portfolio, Ledger, and WhatsApp Funds sections remain here)
