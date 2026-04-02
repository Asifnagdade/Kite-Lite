import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- 2. MASTER DATA (NSE & MCX Contracts) ---
MASTER_DATA = {
    "NSE": {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "SBIN": "SBIN.NS"
    },
    "MCX": {
        "GOLD": "GC=F", "SILVER": "SI=F", "COPPER": "HG=F", "CRUDEOIL": "CL=F",
        "GOLDM": "GOLDM.NS", "NATURALGAS": "NG=F", "ZINC": "ZINC1!S",
        "SILVERM": "SIL=F", "SILVERMIC": "SILMIC.NS", "CRUDEOILM": "QM=F",
        "ZINCMINI": "ZINC-MINI.NS", "NATGASMINI": "QG=F"
    }
}

# --- 3. STYLING ---
st.markdown("""
    <style>
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 5px; height: 45px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE (Admin & User DB) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 100000.0},
        "user1": {"pwd": "1234", "role": "user", "balance": 50000.0}
    }
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 5. PRICE ENGINE (Simulated Bid/Ask & INR) ---
def get_live_market_data(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        ltp = float(data['Close'].iloc[-1])
        if is_mcx:
            ltp = ltp * 83.85 # INR Scale factor
            data['Close'] *= 83.85
            
        ltp += random.uniform(-0.1, 0.1) # Flicker effect
        bid = round(ltp - 0.60, 2)
        ask = round(ltp + 0.60, 2) # Best Ask (High Bid) for Market Buy
        return data, round(ltp, 2), bid, ask
    except: return None, 0.0, 0.0, 0.0

# --- 6. LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 7. SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{u_id.upper()}**")
    st.metric("Balance", f"₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    st.divider()
    seg = st.selectbox("Segment", ["MCX", "NSE"])
    to_add = st.selectbox("Search", list(MASTER_DATA[seg].keys()))
    if st.button("Add to Watchlist"):
        if seg == "NSE": st.session_state.nse_watchlist.append(f"{to_add} FUT")
        else: st.session_state.mcx_watchlist.append(f"{to_add} FUT")
        st.rerun()
    if st.button("Logout"):
        st.session_state.logged_in_user = None; st.rerun()

# --- 8. TABS ---
t_names = ["📊 Terminal", "💼 Portfolio"]
if u_role == "admin": t_names.append("🛠️ Admin Control")
tabs = st.tabs(t_names)

# TERMINAL
with tabs[0]:
    c1, c2 = st.columns(2)
    s_n = c1.selectbox("NSE List", st.session_state.nse_watchlist)
    s_m = c2.selectbox("MCX List", st.session_state.mcx_watchlist)
    active = st.radio("Select View", [s_n, s_m], horizontal=True)
    base = active.split(' ')[0]
    is_mcx = base in MASTER_DATA["MCX"]
    
    df, ltp, bid, ask = get_live_market_data(MASTER_DATA["MCX"].get(base) or MASTER_DATA["NSE"].get(base), is_mcx)

    if ltp > 0:
        col_m, col_o = st.columns([2.5, 1])
        with col_m:
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            st.metric("Market Buy Price (Ask)", f"₹{ask}")
            
        with col_o:
            st.write("### Order Window")
            otype = st.radio("Order", ["Market", "Limit"])
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1)
            exec_p = ask if otype == "Market" else st.number_input("Price", value=ltp)
            
            lev = 500 if "Intraday" in prod else 60
            margin = (exec_p * qty) / lev
            st.write(f"Margin: **₹{margin:,.2f}**")
            
            if st.button("BUY", type="primary"):
                if st.session_state.user_db[u_id]["balance"] < margin: st.error("Low Funds")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({
                        "User": u_id, "Symbol": active, "Avg": exec_p, "Qty": qty, 
                        "Margin": margin, "Time": datetime.now()
                    })
                    st.success("Executed!")

# PORTFOLIO (With 90% Auto-Square Off Logic)
with tabs[1]:
    st.subheader("Active Trades")
    u_portfolio = [p for p in st.session_state.portfolio if p["User"] == u_id]
    
    for pos in u_portfolio:
        # Current P&L calculation based on current bid (exit price)
        pnl = (bid - pos['Avg']) * pos['Qty']
        
        # 90% Loss Check (Auto-Square Off)
        if pnl <= -(pos['Margin'] * 0.90):
            st.warning(f"AUTO-SQUARE OFF: {pos['Symbol']} hit 90% margin erosion!")
            st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
            st.session_state.portfolio.remove(pos)
            st.rerun()
            
        clr = "green" if pnl >= 0 else "red"
        st.write(f"**{pos['Symbol']}** | P&L: :{clr}[₹{pnl:,.2f}]")
        if st.button(f"Exit {pos['Symbol']}"):
            if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                st.error("Hold for 2 mins!")
            else:
                st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.remove(pos)
                st.rerun()

# ADMIN CONTROL
if u_role == "admin":
    with tabs[2]:
        st.header("Admin Dashboard")
        with st.expander("👤 User Management"):
            nu = st.text_input("New Username")
            np = st.text_input("New Password")
            if st.button("Create User"):
                st.session_state.user_db[nu] = {"pwd": np, "role": "user", "balance": 0.0}
                st.success("User Created")
                
        with st.expander("💰 Fund Management"):
            target = st.selectbox("Select User", list(st.session_state.user_db.keys()))
            amt = st.number_input("Amount", step=100.0)
            if st.button("Update Funds"):
                st.session_state.user_db[target]["balance"] += amt
                st.success("Funds Updated")
        
        st.write("### All Users", pd.DataFrame(st.session_state.user_db).T)
