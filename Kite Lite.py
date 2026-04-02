import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite", layout="wide", page_icon="📈")

# --- MASTER DATA (As per your Screenshot) ---
MASTER_DATA = {
    "NSE": {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "SBIN": "SBIN.NS"
    },
    "MCX": {
        "GOLD": "GC=F", "SILVER": "SI=F", "CRUDEOIL": "CL=F", "NATURALGAS": "NG=F",
        "GOLDM": "GOLDM.NS", "SILVERM": "SIL=F", "CRUDEOILM": "QM=F", "NATGASMINI": "QG=F"
    }
}

# --- SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []}}
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOILM"]
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- REAL-TIME PRICE ENGINE (Zerodha Style) ---
def get_pro_price(ticker, is_mcx=False):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty: return None, 0.0, 0.0, 0.0
        
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        ltp = float(data['Close'].iloc[-1])
        
        # MCX INR CONVERSION
        if is_mcx:
            usd_inr = 83.50 # Fallback
            try:
                rate = yf.download("USDINR=X", period="1d", interval="1m", progress=False)['Close'].iloc[-1]
                usd_inr = float(rate)
            except: pass
            ltp = ltp * usd_inr
            data['Close'] *= usd_inr

        # Artificial Fluctuation (Real-time feel)
        fluctuation = random.uniform(-0.0002, 0.0002) * ltp
        ltp += fluctuation
        
        # Market Depth Simulation (Bid/Ask)
        bid = ltp - (ltp * 0.0001) # Best Buyer
        ask = ltp + (ltp * 0.0001) # Best Seller (High Bid for Market Buy)
        
        return data, round(ltp, 2), round(bid, 2), round(ask, 2)
    except:
        return None, 0.0, 0.0, 0.0

# --- LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Professional")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_data = st.session_state.user_db[u_id]

# --- SIDEBAR & DUAL WATCHLIST ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Available Balance", f"₹{u_data['balance']:,.2f}")
    
    st.divider()
    seg = st.selectbox("Segment", ["NSE", "MCX"])
    to_add = st.selectbox("Search", list(MASTER_DATA[seg].keys()))
    if st.button("Add to Watchlist"):
        name = f"{to_add} {datetime.now().strftime('%b').upper()} FUT"
        if seg == "NSE": st.session_state.nse_watchlist.append(name)
        else: st.session_state.mcx_watchlist.append(name)
        st.rerun()

# --- TERMINAL ---
t1, t2, t3 = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Rules"])

with t1:
    c_n, c_m = st.columns(2)
    with c_n: sel_nse = st.selectbox("NSE Scripts", st.session_state.nse_watchlist)
    with c_m: sel_mcx = st.selectbox("MCX Scripts", st.session_state.mcx_watchlist)
    
    active_view = st.radio("Select Trading View", [sel_nse, sel_mcx], horizontal=True)
    base = active_view.split(' ')[0]
    is_mcx = base in MASTER_DATA["MCX"]
    yf_sym = MASTER_DATA["MCX"].get(base) or MASTER_DATA["NSE"].get(base)

    df, ltp, bid, ask = get_pro_price(yf_sym, is_mcx)
    
    if ltp > 0:
        col_chart, col_order = st.columns([3, 1])
        with col_chart:
            st.subheader(f"{active_view}")
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Market Depth UI
            d1, d2 = st.columns(2)
            d1.metric("Best Bid (Sell Price)", f"₹{bid}")
            d2.metric("Best Ask (Buy Price)", f"₹{ask}")
            
        with col_order:
            st.write("### Order Window")
            order_type = st.radio("Order Type", ["Market", "Limit"])
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Quantity", min_value=1, value=1)
            
            # Exec Price Logic
            exec_price = ask if order_type == "Market" else st.number_input("Limit Price", value=ltp)
            
            # Margin Calculation
            lev = 500 if "Intraday" in prod else 60
            margin = (exec_price * qty) / lev
            st.metric("Required Margin", f"₹{margin:,.2f}")
            
            if st.button("BUY / LONG", use_container_width=True, type="primary"):
                if u_data["balance"] < margin:
                    st.error("Insufficient Funds!")
                elif order_type == "Limit" and (exec_price > ltp * 1.04 or exec_price < ltp * 0.96):
                    st.error("Price outside 4% range!")
                else:
                    # Execute Trade
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({
                        "Symbol": active_view, "Price": exec_price, "Qty": qty, 
                        "Type": prod, "Time": datetime.now(), "Margin": margin
                    })
                    st.success(f"Bought at ₹{exec_price}")
    else:
        st.error("Connecting to Exchange... Please wait.")

with t2:
    st.subheader("Running Positions")
    for i, pos in enumerate(st.session_state.portfolio):
        # Current P&L calculation based on latest Bid (to sell)
        pnl = (bid - pos['Price']) * pos['Qty']
        color = "green" if pnl >= 0 else "red"
        st.write(f"**{pos['Symbol']}** | Qty: {pos['Qty']} | Avg: ₹{pos['Price']} | P&L: :{color}[₹{pnl:,.2f}]")
        
        if st.button(f"Square Off {i}", use_container_width=True):
            if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                st.error("Rule: 2-Minute Holding Required!")
            else:
                st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.pop(i)
                st.rerun()

with t3:
    st.info("60x Delivery | 500x Intraday | Market Orders execute at Best Ask (Slippage included) | 2-Min Holding Rule.")
