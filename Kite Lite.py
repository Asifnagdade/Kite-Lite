import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import random

# --- 1. CONFIG & MASTER DATA ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

MASTER_DATA = {
    "NSE": {"NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "SBIN": "SBIN.NS"},
    "MCX": {
        "GOLD": "GC=F", "SILVER": "SI=F", "COPPER": "HG=F", "CRUDEOIL": "CL=F",
        "GOLDM": "GOLDM.NS", "NATURALGAS": "NG=F", "ZINC": "ZINC1!S",
        "SILVERM": "SIL=F", "SILVERMIC": "SILMIC.NS", "CRUDEOILM": "QM=F",
        "ZINCMINI": "ZINC-MINI.NS", "NATGASMINI": "QG=F"
    }
}

# --- 2. SESSION STATE (POORA DATA EK JAGAH) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'watchlists' not in st.session_state: st.session_state.watchlists = {"NSE": ["NIFTY 50"], "MCX": ["CRUDEOILM"], "OPT": [], "MCXOPT": []}
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 3. LOGIN & PASS RESET LOGIC ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
        else: st.error("Invalid Login")
    st.stop()

u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# Force Change Password for New Users
if st.session_state.user_db[u_id].get("first_login", True) and u_role == "user":
    st.warning("Set a new password to continue.")
    new_p = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        st.session_state.user_db[u_id]["pwd"] = new_p
        st.session_state.user_db[u_id]["first_login"] = False; st.rerun()
    st.stop()

# --- 4. ADMIN MASTER PANEL ---
if u_role == "admin":
    st.header("🛠️ Admin Master Panel")
    tabs = st.tabs(["👤 Clients", "💰 Ledger", "📋 Live Trades", "📑 History Audit"])
    
    with tabs[0]: # Client Management
        c1, c2 = st.columns(2)
        with c1:
            nu = st.text_input("Create ID")
            if st.button("Add User"):
                st.session_state.user_db[nu] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                st.success(f"ID {nu} added.")
        with c2:
            ru = st.selectbox("Manage ID", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
            if st.button("Reset Pass to 1234"):
                st.session_state.user_db[ru]["pwd"] = "1234"
                st.session_state.user_db[ru]["first_login"] = True; st.success("Reset Done.")
            if st.button("🗑️ DELETE USER PERMANENTLY"):
                del st.session_state.user_db[ru]; st.rerun()

    with tabs[1]: # Ledger
        tu = st.selectbox("Target Account", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (+/-)")
        if st.button("Commit to Ledger"):
            st.session_state.user_db[tu]["balance"] += amt
            st.session_state.user_db[tu]["ledger"].append({"Date": datetime.now(), "Amt": amt, "Bal": st.session_state.user_db[tu]["balance"]})
            st.success("Updated.")

    with tabs[2]: # Live Positions + Deletion
        for i, pos in enumerate(st.session_state.portfolio):
            st.write(f"{pos['User']} | {pos['Sym']} | Qty: {pos['Qty']}")
            if st.button(f"FORCE DELETE POSITION {i}"):
                st.session_state.portfolio.pop(i); st.rerun()

    with tabs[3]: # Permanent History Deletion
        for i, order in enumerate(st.session_state.order_history):
            st.write(f"{order['User']} | {order['Sym']} | {order['Time']}")
            if st.button(f"DELETE RECORD {i}"):
                st.session_state.order_history.pop(i); st.rerun()

# --- 5. CLIENT SECTION (WATCHLIST & FUNDS) ---
else:
    st.sidebar.metric("Balance", f"₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    if st.sidebar.button("Logout"): st.session_state.logged_in_user = None; st.rerun()

    # Segment Watchlist
    seg = st.radio("Market", ["NSE", "MCX", "OPT", "MCXOPT"], horizontal=True)
    sel_script = st.selectbox("Search", list(MASTER_DATA.get(seg, {}).keys()))
    if st.button("➕ Add to Watchlist"): st.session_state.watchlists[seg].append(sel_script)

    t1, t2, t3 = st.tabs(["📊 Terminal", "📜 Ledger", "💸 Funds"])
    
    with t3: # Pay-in & Payout with WhatsApp
        st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
        val = st.number_input("Amount", min_value=0)
        # Pay-in WhatsApp Redirect
        wa_in = f"https://wa.me/96569304925?text=Payin%20Request:%20{val}%20User:%20{u_id}"
        if st.button("Pay-in via WhatsApp (+965 69304925)"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_in}">', unsafe_allow_html=True)
        
        # Payout Security Check
        if st.button("Payout Request"):
            if val > st.session_state.user_db[u_id]["balance"] or val <= 0: st.error("Insufficient Funds!")
            else:
                wa_out = f"https://wa.me/96569304925?text=Payout%20Request:%20{val}%20User:%20{u_id}"
                st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_out}">', unsafe_allow_html=True)
