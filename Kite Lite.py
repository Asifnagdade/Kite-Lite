import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- 2. MASTER DATA (MCX & NSE) ---
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
if 'watchlists' not in st.session_state: 
    st.session_state.watchlists = {"NSE": ["NIFTY 50"], "MCX": ["CRUDEOILM"], "OPT": [], "MCXOPT": []}
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
        if is_mcx: ltp *= 83.90
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

# --- 6. SIDEBAR (Clean Admin / Detailed User) ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{u_id.upper()}**")
    if u_role == "user":
        st.metric("Available Margin", f"₹{u_data['balance']:,.2f}")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in_user = None; st.rerun()

# --- 7. MAIN INTERFACE ---
if u_role == "admin":
    # ADMIN PANEL: Management Only
    st.header("🛠️ Admin Control")
    tabs = st.tabs(["👤 Clients", "💰 Pay-in/Out Manager", "📑 Audit Logs"])
    
    with tabs[0]:
        nu = st.text_input("New Client Username")
        if st.button("Create Client (Pwd: 1234)"):
            st.session_state.user_db[nu] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": []}
            st.success(f"Client {nu} created.")
        
        st.subheader("Reset Password")
        ru = st.selectbox("Select User", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        np = st.text_input("New Password", "1234")
        if st.button("Update"):
            st.session_state.user_db[ru]['pwd'] = np; st.success("Done")

    with tabs[1]:
        tu = st.selectbox("Target Client", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (+ for Pay-in, - for Payout)")
        rem = st.text_input("Remark (e.g. Cash Deposit)")
        if st.button("Confirm Transaction"):
            st.session_state.user_db[tu]["balance"] += amt
            st.session_state.user_db[tu]["ledger"].append({"Date": datetime.now(), "Type": "Admin Entry", "Amt": amt, "Remark": rem, "Bal": st.session_state.user_db[tu]["balance"]})
            st.success("Ledger Updated")

    with tabs[2]:
        st.table(pd.DataFrame(st.session_state.user_db).T[['role', 'balance']])

else:
    # CLIENT INTERFACE: Full Trading Power
    # Watchlist Header (As per your Image)
    st.markdown("### MarketWatch")
    seg_cols = st.columns(6)
    selected_seg = "NSE"
    if seg_cols[0].button("NSE"): selected_seg = "NSE"
    if seg_cols[1].button("MCX"): selected_seg = "MCX"
    if seg_cols[2].button("OPT"): selected_seg = "OPT"
    if seg_cols[3].button("MCXOPT"): selected_seg = "MCXOPT"
    
    # Search & Add (Image Style)
    c_search, c_add = st.columns([4, 1])
    search_q = c_search.selectbox(f"Search {selected_seg} Script", list(MASTER_DATA.get(selected_seg, {}).keys()))
    if c_add.button("➕ Add"):
        st.session_state.watchlists[selected_seg].append(search_q)
        st.rerun()

    t_trade, t_port, t_ledger, t_pay = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Ledger", "💸 Payin/Payout"])

    with t_trade:
        active_script = st.selectbox("Select from Watchlist", st.session_state.watchlists[selected_seg])
        is_mcx = selected_seg == "MCX"
        df, ltp, bid, ask = get_live_data(MASTER_DATA.get(selected_seg, {}).get(active_script, "^NSEI"), is_mcx)
        
        if ltp > 0:
            cm, co = st.columns([2.5, 1])
            with cm:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, title=active_script)
                st.plotly_chart(fig, use_container_width=True)
            with co:
                st.write("#### Order Window")
                otype = st.radio("Type", ["Market", "Limit"])
                prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
                qty = st.number_input("Qty", 1)
                exec_p = ask if otype == "Market" else st.number_input("Price", value=ltp)
                lev = 500 if "Intraday" in prod else 60
                margin = (exec_p * qty) / lev
                st.metric("Margin Required", f"₹{margin:,.2f}")
                if st.button("BUY / LONG", type="primary"):
                    if u_data["balance"] < margin: st.error("Low Funds")
                    else:
                        st.session_state.user_db[u_id]["balance"] -= margin
                        trade = {"User": u_id, "Sym": active_script, "Avg": exec_p, "Qty": qty, "Margin": margin, "Time": datetime.now()}
                        st.session_state.portfolio.append(trade); st.session_state.order_history.append(trade)
                        st.success("Trade Executed")

    with t_port:
        u_pos = [p for p in st.session_state.portfolio if p["User"] == u_id]
        for p in u_pos:
            pnl = (bid - p['Avg']) * p['Qty']
            if pnl <= -(p['Margin'] * 0.90): # 90% Auto-Exit
                st.session_state.user_db[u_id]["balance"] += (p['Margin'] + pnl)
                st.session_state.portfolio.remove(p); st.rerun()
            st.write(f"**{p['Sym']}** | P&L: ₹{pnl:,.2f}")
            if st.button(f"Exit {p['Sym']}"):
                st.session_state.user_db[u_id]["balance"] += (p['Margin'] + pnl)
                st.session_state.portfolio.remove(p); st.rerun()

    with t_ledger:
        st.table(pd.DataFrame(u_data['ledger']))

    with t_pay:
        st.subheader("Add or Withdraw Funds")
        st.info("For Instant Pay-in, Contact Admin at: **+91-XXXXXXXXXX** (Your Number)")
        pay_type = st.radio("Transaction Type", ["Pay-in Request", "Payout Request"])
        pay_amt = st.number_input("Amount", 100)
        if st.button("Submit Request"):
            st.success("Request sent to Admin. Balance will update after verification.")
