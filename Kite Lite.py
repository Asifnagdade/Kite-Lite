import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- 2. MASTER DATA (MCX Contracts from your list) ---
MASTER_DATA = {
    "NSE": {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS"
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

# --- 4. SESSION STATE (Database) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {"asifnagdade": {"pwd": "Khadija@12", "balance": 100000.0}}
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 5. PRICE ENGINE (Simulated Bid/Ask) ---
def get_live_market_price(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        
        if isinstance(data.columns, pd.MultiIndex): 
            data.columns = data.columns.get_level_values(0)
            
        ltp = float(data['Close'].iloc[-1])
        
        # MCX INR Scaling
        if is_mcx:
            ltp = ltp * 83.85 # Live USDINR approx
            data['Close'] *= 83.85
            data['Open'] *= 83.85
            data['High'] *= 83.85
            data['Low'] *= 83.85
            
        # Real-time Fluctuation
        ltp += random.uniform(-0.2, 0.2)
        bid = round(ltp - 1.0, 2)  # Buyer Price
        ask = round(ltp + 1.0, 2)  # Seller Price (High Bid for execution)
        
        return data, round(ltp, 2), bid, ask
    except:
        return None, 0.0, 0.0, 0.0

# --- 6. LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u = st.text_input("User")
    p = st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user

# --- 7. SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Total Balance", f"₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    st.divider()
    seg = st.selectbox("Segment", ["MCX", "NSE"])
    to_add = st.selectbox("Search Contract", list(MASTER_DATA[seg].keys()))
    if st.button("Add to Watchlist"):
        name = f"{to_add} FUT"
        if seg == "NSE": st.session_state.nse_watchlist.append(name)
        else: st.session_state.mcx_watchlist.append(name)
        st.success(f"{name} Added!")

# --- 8. TERMINAL ---
tab1, tab2 = st.tabs(["📊 Live Terminal", "💼 My Positions"])

with tab1:
    c1, c2 = st.columns(2)
    sel_n = c1.selectbox("NSE List", st.session_state.nse_watchlist)
    sel_m = c2.selectbox("MCX List", st.session_state.mcx_watchlist)
    
    active = st.radio("Focus Script", [sel_n, sel_m], horizontal=True)
    base_name = active.split(' ')[0]
    is_mcx = base_name in MASTER_DATA["MCX"]
    yf_symbol = MASTER_DATA["MCX"].get(base_name) or MASTER_DATA["NSE"].get(base_name)

    df, ltp, bid, ask = get_live_market_price(yf_symbol, is_mcx)

    if ltp > 0:
        col_view, col_order = st.columns([2.5, 1])
        with col_view:
            st.subheader(f"{active} (INR)")
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            m1, m2 = st.columns(2)
            m1.metric("LTP", f"₹{ltp}")
            m2.metric("Market High Bid (Buy At)", f"₹{ask}")

        with col_order:
            st.write("### Order Window")
            otype = st.radio("Order", ["Market", "Limit"])
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1, step=1)
            
            # EXECUTION LOGIC
            # If Market Order -> Executed at Ask (Higher Price)
            exec_p = ask if otype == "Market" else st.number_input("Limit Price", value=ltp)
            
            lev = 500 if "Intraday" in prod else 60
            margin_req = (exec_p * qty) / lev
            st.write(f"Margin Needed: **₹{margin_req:,.2f}**")
            
            if st.button("BUY / LONG", type="primary"):
                if st.session_state.user_db[u_id]["balance"] < margin_req:
                    st.error("Insufficient Margin!")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin_req
                    st.session_state.portfolio.append({
                        "Symbol": active, "Avg": exec_p, "Qty": qty, 
                        "Margin": margin_req, "Time": datetime.now()
                    })
                    st.success(f"Executed @ ₹{exec_p}")

with tab2:
    st.subheader("Positions")
    if not st.session_state.portfolio:
        st.info("No Open Positions")
    else:
        for i, pos in enumerate(st.session_state.portfolio):
            # Exit price is always at BID (What you can sell at)
            curr_pnl = (bid - pos['Avg']) * pos['Qty']
            clr = "green" if curr_pnl >= 0 else "red"
            st.write(f"**{pos['Symbol']}** | Qty: {pos['Qty']} | P&L: :{clr}[₹{curr_pnl:,.2f}]")
            
            if st.button(f"Square Off Position {i}"):
                if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                    st.error("Holding Period Rule: 2 Mins Required")
                else:
                    st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + curr_pnl)
                    st.session_state.portfolio.pop(i)
                    st.rerun()
