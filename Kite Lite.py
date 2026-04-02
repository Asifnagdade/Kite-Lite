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

# --- 3. SESSION STATE (Admin, Orders, Ledger) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []}
    }
if 'watchlists' not in st.session_state: st.session_state.watchlists = {"NSE": ["NIFTY 50"], "MCX": ["CRUDEOILM"], "OPT": [], "MCXOPT": []}
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 4. PRICE ENGINE ---
def get_live_data(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        ltp = float(data['Close'].iloc[-1])
        if is_mcx: ltp *= 83.95
        ltp += random.uniform(-0.1, 0.1)
        bid, ask = round(ltp - 0.50, 2), round(ltp + 0.50, 2)
        return data, round(ltp, 2), bid, ask
    except: return None, 0.0, 0.0, 0.0

# --- 5. LOGIN SYSTEM ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
        else: st.error("Invalid Username or Password")
    st.stop()

u_id = st.session_state.logged_in_user
u_data = st.session_state.user_db[u_id]
u_role = u_data["role"]

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{u_id.upper()}**")
    if u_role == "user": st.metric("Margin Available", f"₹{u_data['balance']:,.2f}")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in_user = None; st.rerun()

# --- 7. MAIN INTERFACE ---
if u_role == "admin":
    st.header("🛠️ Admin Master Panel")
    tabs = st.tabs(["👤 Client Management", "💰 Ledger Control", "📋 Live Order Monitor", "📑 Trade History"])
    
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Add User")
            nu = st.text_input("New Username")
            if st.button("Create Client (Default Pwd: 1234)"):
                st.session_state.user_db[nu] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": []}
                st.success(f"Client {nu} created.")
        with c2:
            st.subheader("Security")
            ru = st.selectbox("Select Account", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
            np = st.text_input("New Password", "1234")
            if st.button("Update Pass"):
                st.session_state.user_db[ru]['pwd'] = np; st.success("Updated")

    with tabs[1]:
        st.subheader("Financial Control")
        tu = st.selectbox("Select Target", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (Pay-in: +, Payout: -)")
        rem = st.text_input("Remark")
        if st.button("Confirm Entry"):
            st.session_state.user_db[tu]["balance"] += amt
            st.session_state.user_db[tu]["ledger"].append({"Date": datetime.now(), "Amt": amt, "Remark": rem, "Bal": st.session_state.user_db[tu]["balance"]})
            st.success("Ledger Updated")

    with tabs[2]:
        st.subheader("Live Open Positions (All Users)")
        if st.session_state.portfolio: st.table(pd.DataFrame(st.session_state.portfolio))
        else: st.info("No open positions.")

    with tabs[3]:
        st.subheader("Executed Order Audit")
        if st.session_state.order_history: st.table(pd.DataFrame(st.session_state.order_history))
        else: st.info("No order history found.")

else:
    # CLIENT INTERFACE (Same as Requested)
    st.markdown("### MarketWatch")
    seg_cols = st.columns(6)
    selected_seg = "NSE"
    if seg_cols[0].button("NSE"): selected_seg = "NSE"
    if seg_cols[1].button("MCX"): selected_seg = "MCX"
    
    c_search, c_add = st.columns([4, 1])
    search_q = c_search.selectbox(f"Search {selected_seg}", list(MASTER_DATA.get(selected_seg, {}).keys()))
    if c_add.button("➕ Add"):
        st.session_state.watchlists[selected_seg].append(search_q)
        st.rerun()

    t_tr, t_po, t_le, t_fu = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Ledger", "💸 Funds"])

    # (Remaining User Trading Logic - Terminal, Portfolio, Ledger, Funds as established before)
