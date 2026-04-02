import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro - CFT", layout="wide", page_icon="💎")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'balance' not in st.session_state: st.session_state.balance = 1000000.0
if 'orders' not in st.session_state: st.session_state.orders = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'wl1' not in st.session_state: st.session_state.wl1 = ["^NSEI", "^NSEBANK"]
if 'wl2' not in st.session_state: st.session_state.wl2 = ["GC=F", "CL=F", "SI=F"]

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.title("🔐 Terminal Login")
        user = st.text_input("User ID", value="USER123")
        pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if user == "USER123" and pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else: st.error("Invalid Credentials")
    st.stop()

# --- SIDEBAR & WATCHLISTS ---
with st.sidebar:
    st.title("💎 CFT Pro Terminal")
    st.metric("Available Balance", f"₹{st.session_state.balance:,.2f}")
    
    wl_choice = st.radio("Select Watchlist", ["Watchlist 1", "Watchlist 2"])
    current_wl = st.session_state.wl1 if wl_choice == "Watchlist 1" else st.session_state.wl2
    
    new_sym = st.text_input("Add Symbol (e.g. RELIANCE.NS)")
    if st.button("Add to Watchlist"):
        if wl_choice == "Watchlist 1": st.session_state.wl1.append(new_sym)
        else: st.session_state.wl2.append(new_sym)
        st.rerun()
    
    ticker = st.selectbox("Select Script", current_wl)
    st.divider()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- RULE VALIDATION FUNCTION ---
def validate_trade(market, margin_required):
    now = datetime.now().time()
    
    # Timing Checks
    if market == "NSE":
        if not (time(9,16) <= now <= time(15,30)): 
            return False, "NSE Market Closed (09:16 - 15:30)"
        if now >= time(15,25): 
            return False, "Trades blocked in last 5 mins (Entry Restriction)"
    else: # MCX
        if not (time(9,1) <= now <= time(23,30)): 
            return False, "MCX Market Closed (09:01 - 23:30)"
        if now >= time(23,25): 
            return False, "Trades blocked in last 5 mins"
    
    # Balance Check
    if st.session_state.balance < margin_required:
        return False, "Insufficient Balance for this trade."
        
    return True, "Valid"

# --- MAIN DASHBOARD ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Terminal", "📝 Trade Log", "💼 Portfolio", "📜 Rules & Regulations"])

# Fetch Data
with st.spinner("Fetching Market Data..."):
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if not data.empty:
        live_price = float(data['Close'][ticker].iloc[-1]) if isinstance(data.columns, pd.MultiIndex) else float(data['Close'].iloc[-1])

# --- TAB 1: TERMINAL ---
with tab1:
    c1, c2 = st.columns([3, 1])
    with c1:
        fig = go.Figure(data=[go.Candlestick(x=data.index,
            open=data['Open'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Open'],
            high=data['High'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['High'],
            low=data['Low'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Low'],
            close=data['Close'][ticker] if isinstance(data.columns, pd.MultiIndex) else data['Close'])])
        fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.info("⚠️ Futures Segment Only")
        st.metric("LTP", f"₹{live_price:,.2f}")
        prod = st.radio("Product Type", ["Intraday (500x)", "Delivery (60x)"])
        qty = st.number_input("Quantity", min_value=1, value=50)
        
        multiplier = 500 if "Intraday" in prod else 60
        margin_needed = (live_price * qty) / multiplier
        st.write(f"**Required Margin:** ₹{margin_needed:,.2f}")

        market_type = "MCX" if ticker in ["GC=F", "CL=F", "SI=F", "NG=F"] else "NSE"
        
        if st.button("BUY / LONG", use_container_width=True, type="primary"):
            ok, msg = validate_trade(market_type, margin_needed)
            if ok:
                st.session_state.balance -= margin_needed
                trade = {"Time": datetime.now().strftime("%H:%M:%S"), "Symbol": ticker, "Type": "BUY", "Qty": qty, "Price": live_price, "Margin": margin_needed}
                st.session_state.orders.append(trade)
                st.session_state.portfolio.append(trade)
                st.success("Trade Executed!")
            else: st.error(msg)

# --- TAB 2: TRADE LOG ---
with tab2:
    st.subheader("Transaction History")
    if st.session_state.orders:
        st.dataframe(pd.DataFrame(st.session_state.orders), use_container_width=True)
    else: st.info("No trades executed yet.")

# --- TAB 3: PORTFOLIO & AUTO SQUARE-OFF LOGIC ---
with tab3:
    st.subheader("Current Positions")
    if st.session_state.portfolio:
        for i, pos in enumerate(st.session_state.portfolio):
            pnl = (live_price - pos['Price']) * pos['Qty'] if pos['Type'] == "BUY" else (pos['Price'] - live_price) * pos['Qty']
            
            # Auto-Square off if loss reaches 90% of Margin
            if pnl <= -(0.9 * pos['Margin']):
                st.warning(f"⚠️ Auto-Squared Off: {pos['Symbol']} reached 90% loss.")
                st.session_state.balance += (pos['Margin'] + pnl) 
                st.session_state.portfolio.pop(i)
                st.rerun()
            
            st.write(f"**{pos['Symbol']}** | Qty: {pos['Qty']} | P&L: :{'green' if pnl>=0 else 'red'}[₹{pnl:,.2f}]")
    else: st.info("No active positions.")

# --- TAB 4: RULES (ENGLISH) ---
with tab4:
    st.header("📋 CFT Compulsory Rules & Regulations")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🔹 NSE Futures Rules")
        st.write("• **Market Hours:** 09:16 AM to 03:30 PM.")
        st.write("• **BTST Restriction:** No new entries allowed in the last 5 minutes of market.")
        st.write("• **Dynamic Square-off:** Position auto-closed at 90% loss of trade margin. New trades can be taken after square-off.")
    with col_b:
        st.subheader("🔹 MCX Futures Rules")
        st.write("• **Market Hours:** 09:01 AM to 11:30 PM.")
        st.write("• **Expiry Rules:** Exit Crude/NG 1 day before expiry; Metals 5 days before.")
        st.write("• **Dynamic Square-off:** Position auto-closed at 90% loss of trade margin.")

    st.error("⚠️ Violation of these rules may lead to trade cancellation.")
