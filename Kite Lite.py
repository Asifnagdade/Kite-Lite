import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Terminal", layout="wide", page_icon="💎")

# --- USER DATABASE (VIRTUAL) ---
# In real-world, this would be a database. For now, it's a session-based dict.
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "admin": {"pwd": "masterpassword", "role": "admin", "balance": 0.0},
        "user1": {"pwd": "user123", "role": "user", "balance": 10000.0},
        "user2": {"pwd": "user456", "role": "user", "balance": 5000.0}
    }

if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'orders' not in st.session_state: st.session_state.orders = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'wl1' not in st.session_state: st.session_state.wl1 = ["^NSEI", "^NSEBANK"]

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in_user:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.title("🔐 Kite Lite Login")
        u_id = st.text_input("User ID")
        u_pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if u_id in st.session_state.user_db and st.session_state.user_db[u_id]["pwd"] == u_pwd:
                st.session_state.logged_in_user = u_id
                st.rerun()
            else: st.error("Invalid Credentials")
    st.stop()

current_user = st.session_state.logged_in_user
user_role = st.session_state.user_db[current_user]["role"]
whatsapp_number = "919000000000" # <-- APNA WHATSAPP NUMBER YAHAN DALEIN

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite Terminal")
    st.write(f"Logged in as: **{current_user.upper()}** ({user_role})")
    
    # User-specific Balance Display
    user_bal = st.session_state.user_db[current_user]["balance"]
    st.metric("Available Balance", f"₹{user_bal:,.2f}")
    
    # PAY-IN / PAY-OUT (WhatsApp Redirect for Users)
    if user_role == "user":
        st.divider()
        st.subheader("Funds Management")
        msg_in = urllib.parse.quote(f"Hello Admin, I ({current_user}) want to PAY-IN funds to my trading account.")
        msg_out = urllib.parse.quote(f"Hello Admin, I ({current_user}) want to PAY-OUT funds from my trading account.")
        
        st.markdown(f'''<a href="https://wa.me/{whatsapp_number}?text={msg_in}" target="_blank"><button style="width:100%; border-radius:5px; background-color:#25D366; color:white; border:none; padding:10px;">Request Pay-in (Add Funds)</button></a>''', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'''<a href="https://wa.me/{whatsapp_number}?text={msg_out}" target="_blank"><button style="width:100%; border-radius:5px; background-color:#f44336; color:white; border:none; padding:10px;">Request Pay-out (Withdraw)</button></a>''', unsafe_allow_html=True)

    st.divider()
    ticker = st.selectbox("Select Script", st.session_state.wl1)
    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- ADMIN PANEL (ONLY FOR MASTER) ---
if user_role == "admin":
    with st.expander("🛠️ MASTER CONTROL PANEL (Admin Only)"):
        st.subheader("Manage User Funds")
        target_user = st.selectbox("Select User", [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"])
        amount = st.number_input("Amount to Add/Subtract", value=0.0)
        if st.button("Update Virtual Funds"):
            st.session_state.user_db[target_user]["balance"] += amount
            st.success(f"Updated {target_user}'s balance to ₹{st.session_state.user_db[target_user]['balance']}")
            st.rerun()

# --- VALIDATION LOGIC ---
def validate_trade(market, margin_required):
    now = datetime.now().time()
    # NSE Rules [cite: 5, 6]
    if market == "NSE":
        if not (time(9,16) <= now <= time(15,30)): return False, "NSE Market Closed [cite: 6]"
        if now >= time(15,25): return False, "Trades blocked in last 5 mins (Rule: No BTST entry) [cite: 19]"
    # MCX Rules [cite: 38, 41]
    else: 
        if not (time(9,1) <= now <= time(23,30)): return False, "MCX Market Closed [cite: 41]"
        if now >= time(23,25): return False, "Trades blocked in last 5 mins"
    
    if st.session_state.user_db[current_user]["balance"] < margin_required:
        return False, "Insufficient Balance for this trade."
    return True, "Valid"

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Terminal", "📝 Trade Log", "💼 Portfolio", "📜 Rules"])

# Data Fetching
data = yf.download(ticker, period="1d", interval="1m", progress=False)
live_price = float(data['Close'].iloc[-1]) if not data.empty else 0.0

# --- TERMINAL & TRADING ---
with tab1:
    if not data.empty:
        c1, c2 = st.columns([3, 1])
        with c1:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("LTP", f"₹{live_price:,.2f}")
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Quantity", min_value=1, value=50)
            mult = 500 if "Intraday" in prod else 60
            margin = (live_price * qty) / mult
            st.write(f"Margin: ₹{margin:,.2f}")
            
            market_type = "MCX" if ticker in ["GC=F", "CL=F"] else "NSE"
            if st.button("BUY", use_container_width=True, type="primary"):
                ok, msg = validate_trade(market_type, margin)
                if ok:
                    st.session_state.user_db[current_user]["balance"] -= margin
                    st.session_state.portfolio.append({"User": current_user, "Symbol": ticker, "Qty": qty, "Price": live_price, "Margin": margin, "Type": "BUY"})
                    st.success("Trade Placed!")
                else: st.error(msg)

# --- PORTFOLIO & AUTO SQUARE-OFF ---
with tab3:
    if st.session_state.portfolio:
        for i, pos in enumerate(st.session_state.portfolio):
            if pos["User"] == current_user:
                pnl = (live_price - pos['Price']) * pos['Qty']
                # 90% Rule [cite: 21, 48]
                if pnl <= -(0.9 * pos['Margin']):
                    st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i)
                    st.warning(f"Position {pos['Symbol']} Auto-Squared Off (90% Loss) [cite: 21]")
                    st.rerun()
                st.write(f"{pos['Symbol']} | P&L: ₹{pnl:,.2f}")
    else: st.info("No active positions.")

# --- RULES (ENGLISH) ---
with tab4:
    st.header("📋 Compulsory Rules & Regulations [cite: 4]")
    st.write("• **NSE Hours:** 09:16 - 15:30 [cite: 6]")
    st.write("• **MCX Hours:** 09:01 - 23:30 [cite: 41]")
    st.write("• **Risk:** Auto-square off at 90% loss of trade capital [cite: 21, 48]")
    st.write("• **BTST:** Not allowed in final 5 minutes [cite: 19]")
