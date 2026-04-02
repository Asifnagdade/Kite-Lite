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
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
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

# --- 6. SIDEBAR (Conditional) ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"User: **{u_id.upper()}**")
    
    # Balance & Watchlist ONLY for Clients
    if u_role == "user":
        st.metric("My Balance", f"₹{u_data['balance']:,.2f}")
        st.divider()
        seg = st.selectbox("Segment", ["MCX", "NSE"])
        to_add = st.selectbox("Search", list(MASTER_DATA[seg].keys()))
        if st.button("Add to Watchlist"):
            name = f"{to_add} FUT"
            if seg == "NSE": st.session_state.nse_watchlist.append(name)
            else: st.session_state.mcx_watchlist.append(name)
            st.rerun()
    
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in_user = None; st.rerun()

# --- 7. MAIN INTERFACE ---
if u_role == "admin":
    # ADMIN VIEW: Focus on Management
    st.header("🛠️ Admin Control Center")
    t1, t2, t3 = st.tabs(["👤 User Management", "💰 Pay-in / Payout", "📋 Live Audit"])
    
    with t1:
        c_a, c_b = st.columns(2)
        with c_a:
            st.subheader("Create New Client")
            nu = st.text_input("New Username")
            if st.button("Create User"):
                if nu not in st.session_state.user_db:
                    st.session_state.user_db[nu] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": []}
                    st.success(f"User {nu} created with 0 balance.")
                else: st.error("User already exists!")
        with c_b:
            st.subheader("Reset Password")
            ru = st.selectbox("Select Client", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
            np = st.text_input("Set Password", value="1234")
            if st.button("Update Password"):
                st.session_state.user_db[ru]["pwd"] = np
                st.success("Password Updated")

    with t2:
        st.subheader("Transaction Manager")
        tu = st.selectbox("Select Target User", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        amt = st.number_input("Amount (+ for Deposit, - for Withdrawal)")
        remark = st.text_input("Entry Note (e.g. Cash Pay-in)")
        if st.button("Process Entry"):
            st.session_state.user_db[tu]["balance"] += amt
            st.session_state.user_db[tu]["ledger"].append({"Date": datetime.now(), "Amount": amt, "Remark": remark, "Closing": st.session_state.user_db[tu]["balance"]})
            st.success("Ledger Updated")

    with t3:
        st.subheader("User Directory")
        st.table(pd.DataFrame(st.session_state.user_db).T[['role', 'balance']])

else:
    # CLIENT VIEW: Full Trading Power
    tabs = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Ledger", "📑 Orders"])
    
    # TERMINAL (Logic: Market Buy @ Ask)
    with tabs[0]:
        c1, c2 = st.columns(2)
        sel_n = c1.selectbox("NSE List", st.session_state.nse_watchlist)
        sel_m = c2.selectbox("MCX List", st.session_state.mcx_watchlist)
        active = st.radio("Select View", [sel_n, sel_m], horizontal=True)
        base = active.split(' ')[0]
        is_mcx = base in MASTER_DATA["MCX"]
        df, ltp, bid, ask = get_live_data(MASTER_DATA["MCX"].get(base) or MASTER_DATA["NSE"].get(base), is_mcx)

        if ltp > 0:
            cm, co = st.columns([2.5, 1])
            with cm:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Market Price (Buy At)", f"₹{ask}")
            with co:
                st.write("### Order Window")
                otype = st.radio("Type", ["Market", "Limit"])
                prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
                qty = st.number_input("Qty", min_value=1)
                exec_p = ask if otype == "Market" else st.number_input("Price", value=ltp)
                lev = 500 if "Intraday" in prod else 60
                margin = (exec_p * qty) / lev
                st.write(f"Margin: **₹{margin:,.2f}**")
                if st.button("PLACE BUY ORDER", type="primary"):
                    if u_data["balance"] < margin: st.error("Low Balance")
                    else:
                        st.session_state.user_db[u_id]["balance"] -= margin
                        trade = {"User": u_id, "Symbol": active, "Avg": exec_p, "Qty": qty, "Margin": margin, "Time": datetime.now(), "Status": "Open"}
                        st.session_state.portfolio.append(trade)
                        st.session_state.order_history.append(trade)
                        st.rerun()

    # PORTFOLIO (Logic: 90% Auto-Square Off)
    with tabs[1]:
        u_pos = [p for p in st.session_state.portfolio if p["User"] == u_id]
        for pos in u_pos:
            pnl = (bid - pos['Avg']) * pos['Qty']
            if pnl <= -(pos['Margin'] * 0.90): # Auto-Exit
                st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.remove(pos); st.rerun()
            st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
            if st.button(f"Square Off {pos['Symbol']}"):
                if (datetime.now() - pos["Time"]) < timedelta(minutes=2): st.error("Hold 2m")
                else:
                    st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.remove(pos); st.rerun()

    with tabs[2]:
        st.table(pd.DataFrame(u_data.get("ledger", [])))
        
    with tabs[3]:
        st.table(pd.DataFrame([o for o in st.session_state.order_history if o["User"] == u_id]))
