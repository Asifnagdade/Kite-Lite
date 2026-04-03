import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Kite Lite - Futures & MCX", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE (Portfolio Management) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 1000000.0  # ₹10 Lakhs Virtual Money
if 'trades' not in st.session_state:
    st.session_state.trades = []

# --- SIDEBAR: ASSET SELECTION ---
st.sidebar.title("💎 Kite Lite Terminal")
segment = st.sidebar.radio("Select Segment", ["NSE Futures (Indices)", "MCX Commodities"])

# Data Lists
nse_futures = {
    "Nifty 50 Future": "^NSEI", 
    "Bank Nifty Future": "^NSEBANK",
    "Fin Nifty Future": "NIFTY_FIN_SERVICE.NS"
}

mcx_list = {
    "Gold (Large)": "GOLD.NS",
    "Gold Mini": "GOLDM.NS",
    "Silver (Large)": "SILVER.NS",
    "Silver Mini": "SILVERM.NS",
    "Silver Micro": "SILVERMIC.NS",
    "Crude Oil": "CRUDEOIL.NS",
    "Crude Oil Mini": "CRUDEOILM.NS",
    "Natural Gas": "NATURALGAS.NS",
    "Natural Gas Mini": "NATGASMINI.NS"
}

if segment == "NSE Futures (Indices)":
    asset_name = st.sidebar.selectbox("Select Index", list(nse_futures.keys()))
    ticker = nse_futures[asset_name]
else:
    asset_name = st.sidebar.selectbox("Select Commodity", list(mcx_list.keys()))
    ticker = mcx_list[asset_name]

# --- MAIN DASHBOARD ---
st.title(f"📊 Trading: {asset_name}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Virtual Balance", f"₹{st.session_state.balance:,.2f}")

# Fetch Price Data
with st.spinner("Fetching Live Prices..."):
    data = yf.Ticker(ticker).history(period="1d", interval="1m")
    if not data.empty:
        live_price = data['Close'].iloc[-1]
        with col2:
            st.metric("Live Price", f"₹{live_price:,.2f}")
        with col3:
            price_change = live_price - data['Open'].iloc[0]
            st.metric("Today's Change", f"{price_change:,.2f}", delta=f"{price_change:,.2f}")
    else:
        st.error("Market is currently closed or Data Unavailable.")
        live_price = 0

# --- TRADING SECTION ---
st.divider()
t_col1, t_col2 = st.columns(2)

with t_col1:
    st.subheader("Place Order")
    qty = st.number_input("Quantity (Lots)", min_value=1, value=1, step=1)
    trade_type = st.radio("Order Type", ["BUY (Long)", "SELL (Short)"], horizontal=True)
    
    if st.button("EXECUTE ORDER"):
        if live_price > 0:
            cost = live_price * qty
            if st.session_state.balance >= cost:
                st.session_state.balance -= cost
                st.session_state.trades.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Asset": asset_name,
                    "Type": trade_type,
                    "Price": round(live_price, 2),
                    "Qty": qty
                })
                st.success(f"Order Placed: {trade_type} {qty} units of {asset_name}")
            else:
                st.error("Insufficient Funds!")
        else:
            st.warning("Cannot trade when price is 0 (Market Closed).")

with t_col2:
    st.subheader("Trade History")
    if st.session_state.trades:
        df = pd.DataFrame(st.session_state.trades)
        st.table(df.tail(5))
    else:
        st.info("No trades executed yet.")

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.warning("⚠️ EDUCATIONAL ONLY: This is a Paper Trading app for Strategy Testing. No real money involved.")