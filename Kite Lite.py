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
    st.session_state.user_db = {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []}}
if 'watchlists' not in st.session_state: st.session_state.watchlists = {"NSE": ["NIFTY 50"], "MCX": ["CRUDEOILM"]}
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 4. LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_data = st.session_state.user_db[u_id]
u_role = u_data["role"]

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{u_id.upper()}**")
    if u_role == "user": st.metric("Available Margin", f"₹{u_data['balance']:,.2f}")
    if st.button("Logout"): st.session_state.logged_in_user = None; st.rerun()

# --- 6. MAIN INTERFACE ---
if u_role == "admin":
    st.header("🛠️ Admin Control")
    t1, t2 = st.tabs(["👤 Clients", "💰 Ledger Entry"])
    with t1:
        nu = st.text_input("New Client")
        if st.button("Create"):
            st.session_state.user_db[nu] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": []}
            st.success("User Created")
    with t2:
        tu = st.selectbox("Client", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (+/-)")
        rem = st.text_input("Remark")
        if st.button("Update"):
            st.session_state.user_db[tu]["balance"] += amt
            st.session_state.user_db[tu]["ledger"].append({"Date": datetime.now(), "Amt": amt, "Rem": rem, "Bal": st.session_state.user_db[tu]["balance"]})
            st.success("Updated")
else:
    t_trade, t_ledger, t_funds = st.tabs(["📊 Terminal", "📜 Ledger", "💸 Funds"])
    
    with t_trade:
        st.info("MarketWatch and Trading Terminal Active")

    with t_ledger:
        if u_data['ledger']: st.table(pd.DataFrame(u_data['ledger']))
        else: st.info("No Transactions")

    with t_funds:
        st.subheader("💰 Add or Withdraw Funds")
        
        # --- PAY-IN SECTION ---
        st.markdown("### 📥 Pay-in (Deposit)")
        st.error("⚠️ **DISCLAIMER**: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
        in_amt = st.number_input("Enter Deposit Amount", min_value=0, step=100, key="in")
        in_url = f"https://wa.me/96569304925?text=Payin%20Request:%20{in_amt}%20for%20User%20{u_id}"
        if st.button("Send Pay-in Request via WhatsApp"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={in_url}">', unsafe_allow_html=True)

        st.divider()

        # --- PAY-OUT SECTION ---
        st.markdown("### 📤 Payout (Withdraw)")
        out_amt = st.number_input("Enter Withdrawal Amount", min_value=0, step=100, key="out")
        bank_details = st.text_area("Enter Bank/UPI Details for Payout")
        
        if st.button("Request Payout"):
            if out_amt <= 0:
                st.warning("Please enter a valid amount.")
            elif out_amt > u_data['balance']:
                st.error(f"Insufficient Funds! Your balance is only ₹{u_data['balance']:,.2f}")
            elif not bank_details:
                st.error("Please provide Bank/UPI details.")
            else:
                out_url = f"https://wa.me/96569304925?text=Payout%20Request:%20{out_amt}%20for%20User%20{u_id}.%20Details:%20{bank_details}"
                st.success("Processing Payout Request...")
                st.markdown(f'<meta http-equiv="refresh" content="0;url={out_url}">', unsafe_allow_html=True)
