import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Futures", layout="wide", page_icon="🚀")

# --- SESSION DATA ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'balance' not in st.session_state: st.session_state.balance = 1000000.0
if 'orders' not in st.session_state: st.session_state.orders = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'wl1' not in st.session_state: st.session_state.wl1 = ["NIFTY24APR-F", "BANKNIFTY24APR-F"]
if 'wl2' not in st.session_state: st.session_state.wl2 = ["GC=F", "SI=F", "CL=F"]

# --- LOGIN ---
if not st.session_state.logged_in:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.title("🔐 Futures Terminal Login")
        user = st.text_input("User ID", value="USER123")
        pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if user == "USER123" and pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# --- SIDEBAR & WATCHLISTS ---
with st.sidebar:
    st.title("🚀 Kite Lite Futures")
    st.metric("Available Margin", f"₹{st.session_state.balance:,.2f}")
    
    wl_tab = st.radio("Watchlist", ["Watchlist 1", "Watchlist 2"])
    current_wl = st.session_state.wl1 if wl_tab == "Watchlist 1" else st.session_state.wl2
    
    new_symbol = st.text_input("Add Future Symbol (e.g. BTC=F, ^NSEI)")
    if st.button("Add to List"):
        if wl_tab == "Watchlist 1": st.session_state.wl1.append(new_symbol)
        else: st.session_state.wl2.append(new_symbol)
        st.rerun()
    
    ticker = st.selectbox("Select Script", current_wl)
    st.divider()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Trading Terminal", "📝 Trade History", "💼 Positions & P&L"])

# --- DATA FETCH ---
with st.spinner("Fetching Live Market..."):
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if not data.empty:
        if isinstance(data.columns, pd.MultiIndex):
            live_price = float(data['Close'][ticker].iloc[-1])
            prev_close = float(data['Open'][ticker].iloc[0])
        else:
            live_price = float(data['Close'].iloc[-1])
            prev_close = float(data['Open'].iloc[0])
        price_chg = live_price - prev_close

# --- TAB 1: TERMINAL ---
with tab1:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader(f"Futures Chart: {ticker}")
        fig = go.Figure(data=[go.Candlestick(x=data.index,
            open=data['Open'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Open'],
            high=data['High'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['High'],
            low=data['Low'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Low'],
            close=data['Close'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Close'])])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.info("⚠️ Futures Only Enabled")
        st.metric("Live Price", f"₹{live_price:,.2f}", f"{price_chg:,.2f}")
        
        product = st.radio("Product Type", ["Intraday (500x)", "Delivery (60x)"])
        # Customize Qty Enabled
        qty = st.number_input("Custom Quantity", min_value=1, value=50, step=1)
        
        # Margin Calculation
        multiplier = 500 if "Intraday" in product else 60
        required_margin = (live_price * qty) / multiplier
        st.write(f"**Required Margin:** ₹{required_margin:,.2f}")

        if st.button("BUY / LONG", use_container_width=True, type="primary"):
            if st.session_state.balance >= required_margin:
                st.session_state.balance -= required_margin
                order = {"Time": datetime.now().strftime("%H:%M:%S"), "Symbol": ticker, "Type": "BUY", "Product": product, "Qty": qty, "Price": live_price, "MarginUsed": required_margin}
                st.session_state.orders.append(order)
                st.session_state.portfolio.append(order)
                st.success(f"Long Position Taken: {qty} Qty")
            else: st.error("Margin Shortfall!")

        if st.button("SELL / SHORT", use_container_width=True):
            if st.session_state.balance >= required_margin:
                st.session_state.balance -= required_margin
                order = {"Time": datetime.now().strftime("%H:%M:%S"), "Symbol": ticker, "Type": "SELL", "Product": product, "Qty": qty, "Price": live_price, "MarginUsed": required_margin}
                st.session_state.orders.append(order)
                st.error(f"Short Position Taken: {qty} Qty")
            else: st.error("Margin Shortfall!")

# --- TAB 2: TRADE HISTORY ---
with tab2:
    st.subheader("Trade Log")
    if st.session_state.orders:
        st.dataframe(pd.DataFrame(st.session_state.orders), use_container_width=True)
    else: st.info("No trades executed.")

# --- TAB 3: POSITIONS ---
with tab3:
    st.subheader("Open Positions")
    if st.session_state.portfolio:
        for item in st.session_state.portfolio:
            current_pnl = (live_price - item['Price']) * item['Qty'] if item['Type'] == "BUY" else (item['Price'] - live_price) * item['Qty']
            st.write(f"🔹 **{item['Symbol']}** | Qty: {item['Qty']} | Type: {item['Product']} | P&L: :{'green' if current_pnl>=0 else 'red'}[₹{current_pnl:,.2f}]")
        st.divider()
        st.metric("Net Unrealized P&L", f"₹{sum((live_price - i['Price']) * i['Qty'] for i in st.session_state.portfolio if i['Symbol'] == ticker):,.2f}")
    else: st.info("No active positions.")
