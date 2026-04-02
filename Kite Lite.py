import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
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

# --- 5. LOGIN ---
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
    tabs = st.tabs(["👤 Client Management", "💰 Pay-in/Out & Ledger", "📑 System Audit"])
    
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Create New User")
            nu = st.text_input("Username")
            if st.button("Add Client (Default Pwd: 1234)"):
                st.session_state.user_db[nu] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": []}
                st.success(f"User {nu} added.")
        with c2:
            st.subheader("Reset Password")
            ru = st.selectbox("Select User", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
            np = st.text_input("New Password", "1234")
            if st.button("Update"):
                st.session_state.user_db[ru]['pwd'] = np; st.success("Updated")

    with tabs[1]:
        st.subheader("Financial Control")
        tu = st.selectbox("Target Account", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (Deposit: +, Withdrawal: -)")
        rem = st.text_input("Transaction Remark")
        if st.button("Commit to Ledger"):
            st.session_state.user_db[tu]["balance"] += amt
            st.session_state.user_db[tu]["ledger"].append({"Date": datetime.now(), "Amt": amt, "Remark": rem, "Closing": st.session_state.user_db[tu]["balance"]})
            st.success("Ledger Updated Successfully.")

    with tabs[2]:
        st.subheader("All User Data")
        st.table(pd.DataFrame(st.session_state.user_db).T[['role', 'balance']])

else:
    # CLIENT INTERFACE (Segment Watchlist & Trading)
    st.markdown("### MarketWatch")
    seg_cols = st.columns(6)
    selected_seg = "NSE"
    if seg_cols[0].button("NSE"): selected_seg = "NSE"
    if seg_cols[1].button("MCX"): selected_seg = "MCX"
    if seg_cols[2].button("OPT"): selected_seg = "OPT"
    if seg_cols[3].button("MCXOPT"): selected_seg = "MCXOPT"
    
    c_search, c_add = st.columns([4, 1])
    search_q = c_search.selectbox(f"Search {selected_seg}", list(MASTER_DATA.get(selected_seg, {}).keys()))
    if c_add.button("➕ Add"):
        st.session_state.watchlists[selected_seg].append(search_q)
        st.rerun()

    t_tr, t_po, t_le, t_fu = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Ledger", "💸 Funds"])

    with t_tr:
        active_s = st.selectbox("Watchlist", st.session_state.watchlists[selected_seg])
        df, ltp, bid, ask = get_live_data(MASTER_DATA.get(selected_seg, {}).get(active_s, "^NSEI"), (selected_seg == "MCX"))
        if ltp > 0:
            cm, co = st.columns([2.5, 1])
            with cm:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", height=350, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            with co:
                qty = st.number_input("Qty", 1)
                exec_p = ask # Market Buy at Ask
                lev = 500 if selected_seg == "NSE" else 60
                margin = (exec_p * qty) / lev
                st.metric("Margin Required", f"₹{margin:,.2f}")
                if st.button("BUY", type="primary"):
                    if u_data["balance"] < margin: st.error("Low Balance")
                    else:
                        st.session_state.user_db[u_id]["balance"] -= margin
                        st.session_state.portfolio.append({"User": u_id, "Sym": active_s, "Avg": exec_p, "Qty": qty, "Margin": margin, "Time": datetime.now()})
                        st.rerun()

    with t_po:
        u_p = [p for p in st.session_state.portfolio if p["User"] == u_id]
        for p in u_p:
            pnl = (bid - p['Avg']) * p['Qty']
            if pnl <= -(p['Margin'] * 0.90): # 90% Auto-Exit Rule
                st.session_state.user_db[u_id]["balance"] += (p['Margin'] + pnl)
                st.session_state.portfolio.remove(p); st.rerun()
            st.write(f"**{p['Sym']}** | P&L: ₹{pnl:,.2f}")
            if st.button(f"Square Off {p['Sym']}"):
                st.session_state.user_db[u_id]["balance"] += (p['Margin'] + pnl)
                st.session_state.portfolio.remove(p); st.rerun()

    with t_le:
        if u_data['ledger']: st.table(pd.DataFrame(u_data['ledger']))
        else: st.info("No Transactions.")

    with t_fu:
        st.error("⚠️ **DISCLAIMER**: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
        in_amt = st.number_input("Pay-in Amount", min_value=0, step=100)
        wa_url = f"https://wa.me/96569304925?text=Payin%20Request:%20{in_amt}%20User:%20{u_id}"
        if st.button("Pay-in via WhatsApp"):
            st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_url}">', unsafe_allow_html=True)
        
        st.divider()
        out_amt = st.number_input("Payout Amount", min_value=0, step=100)
        details = st.text_area("Bank Details")
        if st.button("Request Payout"):
            if out_amt > u_data['balance']: st.error("Insufficient Funds!")
            else:
                out_url = f"https://wa.me/96569304925?text=Payout%20Request:%20{out_amt}%20User:%20{u_id}%20Details:%20{details}"
                st.markdown(f'<meta http-equiv="refresh" content="0;url={out_url}">', unsafe_allow_html=True)
