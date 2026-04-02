import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- MASTER DATA (As per your MCX screenshot) ---
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

# --- STYLING (Fixed Error) ---
st.markdown("""
    <style>
    .stMetric { background-color: #262626; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 5px; height: 45px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 100000.0}}
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- PRICE ENGINE ---
def get_live_data(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        ltp = float(data['Close'].iloc[-1])
        if is_mcx:
            # Multiplier for INR conversion
            ltp = ltp * 83.70 
            data['Close'] *= 83.70
        
        # Adding Real-time Flicker
        ltp += random.uniform(-0.10, 0.10)
        bid = round(ltp - 0.50, 2)
        ask = round(ltp + 0.50, 2) # High Bid for Market execution
        
        return data, round(ltp, 2), bid, ask
    except: return None, 0.0, 0.0, 0.0

# --- LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Balance", f"₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    st.divider()
    seg = st.selectbox("Segment", ["MCX", "NSE"])
    to_add = st.selectbox("Search", list(MASTER_DATA[seg].keys()))
    if st.button("Add to List"):
        name = f"{to_add} FUT"
        if seg == "NSE": st.session_state.nse_watchlist.append(name)
        else: st.session_state.mcx_watchlist.append(name)
        st.rerun()

# --- TERMINAL ---
t1, t2 = st.tabs(["📊 Terminal", "💼 Portfolio"])

with t1:
    c1, c2 = st.columns(2)
    sel_nse = c1.selectbox("NSE Watchlist", st.session_state.nse_watchlist)
    sel_mcx = c2.selectbox("MCX Watchlist", st.session_state.mcx_watchlist)
    
    active = st.radio("View", [sel_nse, sel_mcx], horizontal=True)
    base = active.split(' ')[0]
    is_mcx = base in MASTER_DATA["MCX"]
    yf_sym = MASTER_DATA["MCX"].get(base) or MASTER_DATA["NSE"].get(base)

    df, ltp, bid, ask = get_live_data(yf_sym, is_mcx)

    if ltp > 0:
        col_main, col_order = st.columns([2.5, 1])
        with col_main:
            st.subheader(active)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Depth UI
            d1, d2 = st.columns(2)
            d1.metric("Best Bid", f"₹{bid}")
            d2.metric("Best Ask (Buy Price)", f"₹{ask}")

        with col_order:
            st.write("### Order")
            o_type = st.radio("Type", ["Market", "Limit"])
            variety = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1, step=1)
            
            # RULE: Market Order executes at ASK (High Bid)
            exec_p = ask if o_type == "Market" else st.number_input("Limit Price", value=ltp)
            
            lev = 500 if "Intraday" in variety else 60
            margin = (exec_p * qty) / lev
            st.metric("Margin Req.", f"₹{margin:,.2f}")
            
            if st.button("BUY", type="primary"):
                if st.session_state.user_db[u_id]["balance"] < margin: st.error("Low Funds")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({"Symbol": active, "Price": exec_p, "Qty": qty, "Type": variety, "Time": datetime.now(), "Margin": margin})
                    st.success(f"Bought @ {exec_p}")

with t2:
    for i, pos in enumerate(st.session_state.portfolio):
        pnl = (bid - pos['Price']) * pos['Qty']
        st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
        if st.button(f"Square Off {i}"):
            if (datetime.now() - pos["Time"]) < timedelta(minutes=2): st.error("Wait 2 mins!")
            else:
                st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.pop(i); st.rerun()import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- MASTER DATA (As per your MCX screenshot) ---
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

# --- STYLING (Fixed Error) ---
st.markdown("""
    <style>
    .stMetric { background-color: #262626; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 5px; height: 45px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 100000.0}}
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- PRICE ENGINE ---
def get_live_data(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        ltp = float(data['Close'].iloc[-1])
        if is_mcx:
            # Multiplier for INR conversion
            ltp = ltp * 83.70 
            data['Close'] *= 83.70
        
        # Adding Real-time Flicker
        ltp += random.uniform(-0.10, 0.10)
        bid = round(ltp - 0.50, 2)
        ask = round(ltp + 0.50, 2) # High Bid for Market execution
        
        return data, round(ltp, 2), bid, ask
    except: return None, 0.0, 0.0, 0.0

# --- LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Balance", f"₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    st.divider()
    seg = st.selectbox("Segment", ["MCX", "NSE"])
    to_add = st.selectbox("Search", list(MASTER_DATA[seg].keys()))
    if st.button("Add to List"):
        name = f"{to_add} FUT"
        if seg == "NSE": st.session_state.nse_watchlist.append(name)
        else: st.session_state.mcx_watchlist.append(name)
        st.rerun()

# --- TERMINAL ---
t1, t2 = st.tabs(["📊 Terminal", "💼 Portfolio"])

with t1:
    c1, c2 = st.columns(2)
    sel_nse = c1.selectbox("NSE Watchlist", st.session_state.nse_watchlist)
    sel_mcx = c2.selectbox("MCX Watchlist", st.session_state.mcx_watchlist)
    
    active = st.radio("View", [sel_nse, sel_mcx], horizontal=True)
    base = active.split(' ')[0]
    is_mcx = base in MASTER_DATA["MCX"]
    yf_sym = MASTER_DATA["MCX"].get(base) or MASTER_DATA["NSE"].get(base)

    df, ltp, bid, ask = get_live_data(yf_sym, is_mcx)

    if ltp > 0:
        col_main, col_order = st.columns([2.5, 1])
        with col_main:
            st.subheader(active)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Depth UI
            d1, d2 = st.columns(2)
            d1.metric("Best Bid", f"₹{bid}")
            d2.metric("Best Ask (Buy Price)", f"₹{ask}")

        with col_order:
            st.write("### Order")
            o_type = st.radio("Type", ["Market", "Limit"])
            variety = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1, step=1)
            
            # RULE: Market Order executes at ASK (High Bid)
            exec_p = ask if o_type == "Market" else st.number_input("Limit Price", value=ltp)
            
            lev = 500 if "Intraday" in variety else 60
            margin = (exec_p * qty) / lev
            st.metric("Margin Req.", f"₹{margin:,.2f}")
            
            if st.button("BUY", type="primary"):
                if st.session_state.user_db[u_id]["balance"] < margin: st.error("Low Funds")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({"Symbol": active, "Price": exec_p, "Qty": qty, "Type": variety, "Time": datetime.now(), "Margin": margin})
                    st.success(f"Bought @ {exec_p}")

with t2:
    for i, pos in enumerate(st.session_state.portfolio):
        pnl = (bid - pos['Price']) * pos['Qty']
        st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
        if st.button(f"Square Off {i}"):
            if (datetime.now() - pos["Time"]) < timedelta(minutes=2): st.error("Wait 2 mins!")
            else:
                st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.pop(i); st.rerun()
