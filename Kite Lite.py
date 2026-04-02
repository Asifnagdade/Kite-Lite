import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Terminal", layout="wide", page_icon="💎")

# --- SIDEBAR / NAVIGATION ---
with st.sidebar:
    st.title("💎 Kite Lite Terminal")
    
    segment = st.radio("Select Segment", ["NSE Futures (Indices)", "MCX Commodities"])
    
    if segment == "NSE Futures (Indices)":
        indices = {
            "Nifty 50 Future": "^NSEI",
            "Bank Nifty Future": "^NSEBANK",
            "Nifty IT Future": "^CNXIT"
        }
        selected_index = st.selectbox("Select Index", list(indices.keys()))
        ticker = indices[selected_index]
    else:
        commodities = {
            "Gold": "GC=F",
            "Silver": "SI=F",
            "Crude Oil": "CL=F",
            "Natural Gas": "NG=F"
        }
        selected_comm = st.selectbox("Select Commodity", list(commodities.keys()))
        ticker = commodities[selected_comm]

# --- MAIN DASHBOARD ---
st.title(f"📊 Trading: {selected_index if segment == 'NSE Futures (Indices)' else selected_comm}")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("Virtual Balance: **₹1,000,000.00**")

# --- DATA FETCHING & DISPLAY ---
with st.spinner("Fetching Data..."):
    # Using download with progress=False to avoid rate limits
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    
    if not data.empty:
        # Handling Multi-index columns in newer yfinance versions
        if isinstance(data.columns, pd.MultiIndex):
            live_price = float(data['Close'][ticker].iloc[-1])
            prev_close = float(data['Open'][ticker].iloc[0])
        else:
            live_price = float(data['Close'].iloc[-1])
            prev_close = float(data['Open'].iloc[0])
            
        price_chg = live_price - prev_close
        
        with col2:
            st.metric("Live Price", f"₹{live_price:,.2f}", f"{price_chg:,.2f}")
            
        # --- CHART SECTION ---
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Open'],
            high=data['High'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['High'],
            low=data['Low'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Low'],
            close=data['Close'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Close'],
            name="Market Data"
        )])
        
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=500,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Market Data is currently unavailable. Please check the ticker or try again later.")

# --- TRADING SECTION ---
st.divider()
t_col1, t_col2 = st.columns(2)

with t_col1:
    qty = st.number_input("Quantity (Lots)", min_value=1, value=1)
    if st.button("BUY", use_container_width=True, type="primary"):
        st.success(f"Order Executed! Bought {qty} lot(s) at ₹{live_price:,.2f}")

with t_col2:
    st.write("") # Alignment
    if st.button("SELL", use_container_width=True):
        st.error(f"Order Executed! Sold {qty} lot(s) at ₹{live_price:,.2f}")

st.caption("Note: This is a Paper Trading terminal for educational purposes.")
