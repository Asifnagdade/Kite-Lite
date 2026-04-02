import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- MASTER DATA ---
MASTER_DATA = {
    "NSE": {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", 
        "SBIN": "SBIN.NS", "TATA MOTORS": "TATAMOTORS.NS"
    },
    "MCX": {
        "GOLD": "GC=F", "SILVER": "SI=F", "COPPER": "HG=F", "CRUDEOIL": "CL=F",
        "GOLDM": "GOLDM.NS", "NATURALGAS": "NG=F", "ZINC": "ZINC1!S",
        "SILVERM": "SIL=F", "SILVERMIC": "SILMIC.NS", "CRUDEOILM": "QM=F",
        "ZINCMINI": "ZINC-MINI.NS", "NATGASMINI": "QG=F"
    }
}

# --- SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 100000.0, "ledger": []}}
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #1a1a1a; }
    .stMetric { background-color: #262626; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 5px; height: 45px; font-weight: bold; }
    .buy-btn { background-color: #4184f3 !important; color: white; }
    .sell-btn { background-color: #df514a !important; color: white; }
    </style>
    """, unsafe_allow_stdio=True)

# --- PRICE ENGINE ---
def get_live_pro_data(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        ltp = float(data['Close'].iloc[-1])
        if is_mcx:
            ltp = ltp * 83.65 # Current Approx USDINR
            data['Close'] *= 83.65
        
        # Fluctuation simulation
        ltp += random.uniform(-0.5, 0.5)
        bid = round(ltp - 1.25, 2)
        ask = round(ltp + 1.25, 2) # Best Ask (High Bid for Buying)
        
        return data, round(ltp, 2), bid, ask
    except: return None, 0.0, 0.0, 0.0

# --- LOGIN ---
if not st.session_state.logged_in_user:
    cols = st.columns([1,1.5,1])
    with cols[1]:
        st.title("🔐 Kite Lite Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
                st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_data = st.session_state.user_db[u_id]

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Balance", f"₹{u_data['balance']:,.2f}")
    st.divider()
    
    add_seg = st.selectbox("Segment", ["NSE", "MCX"])
    to_add = st.selectbox("Search Contract", list(MASTER_DATA[add_seg].keys()))
    if st.button("Add to Watchlist"):
        name = f"{to_add} {datetime.now().strftime('%b').upper()} FUT"
        if add_seg == "NSE": st.session_state.nse_watchlist.append(name)
        else: st.session_state.mcx_watchlist.append(name)
        st.rerun()

# --- MAIN TERMINAL ---
t1, t2, t3 = st.tabs(["📊 Market Watch", "💼 Portfolio", "📜 Trading Rules"])

with t1:
    # Dual Watchlist Selectors
    c_nse, c_mcx = st.columns(2)
    sel_nse = c_nse.selectbox("📈 NSE Stocks", st.session_state.nse_watchlist)
    sel_mcx = c_mcx.selectbox("🧱 MCX Commodities", st.session_state.mcx_watchlist)
    
    active_script = st.radio("Active View", [sel_nse, sel_mcx], horizontal=True)
    base = active_script.split(' ')[0]
    is_mcx = base in MASTER_DATA["MCX"]
    yf_sym = MASTER_DATA["MCX"].get(base) or MASTER_DATA["NSE"].get(base)

    df, ltp, bid, ask = get_live_pro_data(yf_sym, is_mcx)

    if ltp > 0:
        col_main, col_order = st.columns([2.5, 1])
        
        with col_main:
            st.subheader(active_script)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # Simulated Market Depth
            st.write("---")
            md_c1, md_c2 = st.columns(2)
            with md_c1:
                st.write("**Bids (Buy)**")
                st.table(pd.DataFrame({'Price': [bid, bid-1, bid-2], 'Qty': [500, 1200, 850]}))
            with md_c2:
                st.write("**Offers (Sell)**")
                st.table(pd.DataFrame({'Price': [ask, ask+1, ask+2], 'Qty': [300, 950, 1100]}))

        with col_order:
            st.write("### Place Order")
            o_type = st.radio("Order Type", ["Market", "Limit"])
            variety = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Quantity", min_value=1, step=1)
            
            # Logic: Market Buy goes to 'Ask' (High Bid/Seller Price)
            exec_p = ask if o_type == "Market" else st.number_input("Price", value=ltp)
            
            lev = 500 if "Intraday" in variety else 60
            margin = (exec_p * qty) / lev
            st.metric("Required Margin", f"₹{margin:,.2f}")
            
            if st.button("BUY", type="primary"):
                if u_data["balance"] < margin: st.error("Insufficient Funds")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({
                        "Symbol": active_script, "Price": exec_p, "Qty": qty, 
                        "Type": variety, "Time": datetime.now(), "Margin": margin
                    })
                    st.success(f"Bought at ₹{exec_p}")

with t2:
    st.subheader("Positions")
    if not st.session_state.portfolio:
        st.info("No active trades.")
    else:
        for i, pos in enumerate(st.session_state.portfolio):
            current_pnl = (bid - pos['Price']) * pos['Qty']
            color = "green" if current_pnl >= 0 else "red"
            st.write(f"**{pos['Symbol']}** | Avg: ₹{pos['Price']} | P&L: :{color}[₹{current_pnl:,.2f}]")
            if st.button(f"Square Off {i}"):
                if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                    st.error("Hold for 2 mins!")
                else:
                    st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + current_pnl)
                    st.session_state.portfolio.pop(i); st.rerun()

with t3:
    st.markdown("""
    1. **Leverage:** Intraday 500x, Delivery 60x.
    2. **Market Buy:** Executes at Best Ask (Sell Price).
    3. **Holding:** 2-minute mandatory holding rule.
    4. **Auto-Exit:** 90% margin erosion leads to auto square-off.
    """)
