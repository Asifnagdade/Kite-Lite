import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="💎")

# --- LOGIN SYSTEM (Simulated) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.title("🔐 Login to Kite Lite")
        user = st.text_input("User ID", value="USER123")
        pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if user == "USER123" and pwd == "1234": # Simple check
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid ID or Password")
    st.stop()

# --- INITIALIZING SESSION DATA ---
if 'balance' not in st.session_state:
    st.session_state.balance = 1000000.0
if 'orders' not in st.session_state:
    st.session_state.orders = [] # List of dicts
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {} # {ticker: {qty: X, avg_price: Y}}

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite Pro")
    st.write(f"👤 User: **USER123**")
    st.success(f"💰 Balance: ₹{st.session_state.balance:,.2f}")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    segment = st.radio("Market", ["NSE Futures", "MCX Commodities"])
    ticker_map = {
        "Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK", 
        "Gold": "GC=F", "Crude Oil": "CL=F"
    }
    selected_name = st.selectbox("Select Asset", list(ticker_map.keys()))
    ticker = ticker_map[selected_name]

# --- TABS SYSTEM ---
tab1, tab2, tab3 = st.tabs(["📊 Terminal", "📝 Orders", "💼 Portfolio"])

# --- TAB 1: TERMINAL ---
with tab1:
    with st.spinner("Loading Market..."):
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not data.empty:
            # Multi-index fix
            if isinstance(data.columns, pd.MultiIndex):
                live_price = float(data['Close'][ticker].iloc[-1])
                prev_close = float(data['Open'][ticker].iloc[0])
            else:
                live_price = float(data['Close'].iloc[-1])
                prev_close = float(data['Open'].iloc[0])

            c1, c2 = st.columns([2, 1])
            with c1:
                fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Open'],
                    high=data['High'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['High'],
                    low=data['Low'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Low'],
                    close=data['Close'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Close'])])
                fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.metric("Live Price", f"₹{live_price:,.2f}", f"{live_price-prev_close:,.2f}")
                qty = st.number_input("Lots", min_value=1, step=1)
                if st.button("BUY", use_container_width=True, type="primary"):
                    cost = live_price * qty
                    if st.session_state.balance >= cost:
                        st.session_state.balance -= cost
                        # Add to Portfolio
                        p = st.session_state.portfolio.get(selected_name, {'qty': 0, 'avg': 0})
                        new_qty = p['qty'] + qty
                        p['avg'] = ((p['avg'] * p['qty']) + cost) / new_qty
                        p['qty'] = new_qty
                        st.session_state.portfolio[selected_name] = p
                        # Add to Orders
                        st.session_state.orders.append({"Time": datetime.now().strftime("%H:%M:%S"), "Type": "BUY", "Asset": selected_name, "Qty": qty, "Price": live_price, "Status": "Executed"})
                        st.success("Order Placed!")
                    else: st.error("Insufficient Funds")
                
                if st.button("SELL", use_container_width=True):
                    p = st.session_state.portfolio.get(selected_name, {'qty': 0})
                    if p['qty'] >= qty:
                        st.session_state.balance += (live_price * qty)
                        p['qty'] -= qty
                        st.session_state.orders.append({"Time": datetime.now().strftime("%H:%M:%S"), "Type": "SELL", "Asset": selected_name, "Qty": qty, "Price": live_price, "Status": "Executed"})
                        st.warning("Position Closed!")
                    else: st.error("Not enough quantity in portfolio")

# --- TAB 2: ORDERS ---
with tab2:
    st.subheader("Order History")
    if st.session_state.orders:
        st.table(pd.DataFrame(st.session_state.orders))
    else: st.info("No orders yet.")

# --- TAB 3: PORTFOLIO & LIVE P&L ---
with tab3:
    st.subheader("Your Holdings")
    total_pnl = 0
    if st.session_state.portfolio:
        for asset, details in st.session_state.portfolio.items():
            if details['qty'] > 0:
                current_val = live_price * details['qty'] if asset == selected_name else details['avg'] * details['qty'] # Simple simulation
                pnl = (live_price - details['avg']) * details['qty'] if asset == selected_name else 0
                total_pnl += pnl
                st.write(f"**{asset}** | Qty: {details['qty']} | Avg: ₹{details['avg']:.2f} | P&L: :{'green' if pnl>=0 else 'red'}[₹{pnl:,.2f}]")
        st.divider()
        st.metric("Total Unrealized P&L", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
    else: st.info("Portfolio is empty.")
