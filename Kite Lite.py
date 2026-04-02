import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Terminal", layout="wide", page_icon="💎")

# --- MASTER DATABASE INITIALIZATION ---
if 'user_db' not in st.session_state:
    # Initial Database with Admin and one Default User
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "needs_reset": False},
        "user1": {"pwd": "1234", "role": "user", "balance": 10000.0, "needs_reset": True}
    }

if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'orders' not in st.session_state: st.session_state.orders = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'wl1' not in st.session_state: st.session_state.wl1 = ["^NSEI", "^NSEBANK", "GC=F", "CL=F"]

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in_user:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.title("🔐 Kite Lite Login")
        u_id = st.text_input("Username")
        u_pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if u_id in st.session_state.user_db and st.session_state.user_db[u_id]["pwd"] == u_pwd:
                st.session_state.logged_in_user = u_id
                st.rerun()
            else: st.error("Invalid Username or Password")
    st.stop()

current_user = st.session_state.logged_in_user
user_data = st.session_state.user_db[current_user]

# --- PASSWORD RESET FORCE SCREEN ---
if user_data.get("needs_reset", False):
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.warning("🔒 First Time Login: Please reset your password to continue.")
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if new_p == conf_p and len(new_p) > 3:
                st.session_state.user_db[current_user]["pwd"] = new_p
                st.session_state.user_db[current_user]["needs_reset"] = False
                st.success("Password Updated! Redirecting...")
                st.rerun()
            else: st.error("Passwords do not match or too short.")
    st.stop()

# --- APP LOGIC AFTER LOGIN & RESET ---
user_role = user_data["role"]
whatsapp_number = "919000000000" 

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite Terminal")
    st.write(f"User: **{current_user}** ({user_role.upper()})")
    st.metric("Available Balance", f"₹{user_data['balance']:,.2f}")
    
    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()
    st.divider()
    ticker = st.selectbox("Select Script", st.session_state.wl1)

# --- MASTER ADMIN PANEL ---
if user_role == "admin":
    with st.expander("🛠️ MASTER CONTROL PANEL"):
        t1, t2 = st.tabs(["👤 User Management", "💰 Fund Management"])
        
        with t1:
            st.subheader("Create New User")
            new_username = st.text_input("New Username (e.g., user2)")
            if st.button("Create Account"):
                if new_username and new_username not in st.session_state.user_db:
                    st.session_state.user_db[new_username] = {
                        "pwd": "1234", 
                        "role": "user", 
                        "balance": 0.0, 
                        "needs_reset": True
                    }
                    st.success(f"User '{new_username}' created with default password '1234'")
                else: st.error("User already exists or invalid name.")
            
            st.divider()
            st.subheader("Reset User Password")
            user_to_reset = st.selectbox("Select User to Reset", [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"])
            if st.button("Reset to Default (1234)"):
                st.session_state.user_db[user_to_reset]["pwd"] = "1234"
                st.session_state.user_db[user_to_reset]["needs_reset"] = True
                st.warning(f"Password for {user_to_reset} has been reset to 1234.")

        with t2:
            st.subheader("Manage Funds")
            target = st.selectbox("Select Client", [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"], key="fund_sel")
            amt = st.number_input("Add/Subtract Amount", value=0.0)
            if st.button("Update Balance"):
                st.session_state.user_db[target]["balance"] += amt
                st.success("Balance Updated.")
                st.rerun()

# --- DATA FETCHING & VALIDATION ---
def get_live_data(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, float(df['Close'].iloc[-1])
    return df, 0.0

def validate_trade(market, margin_required):
    now = datetime.now().time()
    if market == "NSE":
        if not (time(9,16) <= now <= time(15,30)): return False, "NSE Market Closed [cite: 6]"
    else:
        if not (time(9,1) <= now <= time(23,30)): return False, "MCX Market Closed [cite: 41]"
    
    if st.session_state.user_db[current_user]["balance"] < margin_required:
        return False, "Insufficient Balance."
    return True, "Valid"

# --- MAIN INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Terminal", "📝 Trade Log", "💼 Portfolio", "📜 Rules"])

data, live_price = get_live_data(ticker)

with tab1:
    if not data.empty:
        c1, c2 = st.columns([3, 1])
        with c1:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("LTP", f"₹{live_price:,.2f}")
            qty = st.number_input("Quantity", min_value=1, value=50)
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            mult = 500 if "Intraday" in prod else 60
            margin = (live_price * qty) / mult
            st.write(f"Margin: ₹{margin:,.2f}")
            
            market_type = "MCX" if ticker in ["GC=F", "CL=F", "SI=F", "NG=F"] else "NSE"
            if st.button("PLACE ORDER", use_container_width=True, type="primary"):
                ok, msg = validate_trade(market_type, margin)
                if ok:
                    st.session_state.user_db[current_user]["balance"] -= margin
                    trade = {"Time": datetime.now().strftime("%H:%M:%S"), "Symbol": ticker, "Qty": qty, "Price": live_price, "Margin": margin, "User": current_user}
                    st.session_state.orders.append(trade); st.session_state.portfolio.append(trade)
                    st.success("Trade Successful!")
                else: st.error(msg)

with tab3:
    st.subheader("Active Positions")
    for i, pos in enumerate(st.session_state.portfolio):
        if pos["User"] == current_user:
            pnl = (live_price - pos['Price']) * pos['Qty']
            if pnl <= -(0.9 * pos['Margin']): # 90% Capital Loss Rule [cite: 21, 48]
                st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.pop(i); st.rerun()
            st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")

with tab4:
    st.header("📋 Compulsory Rules & Regulations [cite: 4]")
    c_a, c_b = st.columns(2)
    with c_a:
        st.subheader("NSE Futures [cite: 5]")
        st.write("• Hours: 09:16 to 03:30 [cite: 6]")
        st.write("• Limit Order Max 4% of LTP [cite: 11]")
        st.write("• Auto-square off at 90% capital loss [cite: 21]")
    with c_b:
        st.subheader("MCX Futures [cite: 38]")
        st.write("• Hours: 09:01 to 23:30 [cite: 41]")
        st.write("• Exit Crude/NG 1 day before expiry [cite: 56]")
        st.write("• Auto-square off at 90% capital loss [cite: 48]")
