import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Terminal", layout="wide", page_icon="💎")

# --- DATABASE INITIALIZATION ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "needs_reset": False},
        "user1": {"pwd": "1234", "role": "user", "balance": 10000.0, "needs_reset": True}
    }

if 'banned_scripts' not in st.session_state:
    st.session_state.banned_scripts = [] 

if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = []

# --- NSE & MCX WATCHLIST ---
if 'wl_nse' not in st.session_state:
    st.session_state.wl_nse = ["^NSEI", "^NSEBANK", "RELIANCE.NS", "SBIN.NS", "HDFCBANK.NS"]
if 'wl_mcx' not in st.session_state:
    st.session_state.wl_mcx = ["GC=F", "CL=F", "SI=F", "NG=F"] # Gold, Crude, Silver, Natural Gas

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
            else: st.error("Ghalat Credentials!")
    st.stop()

current_user = st.session_state.logged_in_user
user_data = st.session_state.user_db[current_user]

if user_data.get("needs_reset", False):
    st.warning("🔒 Pehli baar login: Password badalna zaroori hai.")
    new_p = st.text_input("Naya Password", type="password")
    if st.button("Save Password"):
        st.session_state.user_db[current_user]["pwd"] = new_p
        st.session_state.user_db[current_user]["needs_reset"] = False
        st.rerun()
    st.stop()

# --- SIDEBAR & ADMIN PANEL ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{current_user}**")
    st.metric("Balance", f"₹{user_data['balance']:,.2f}")
    
    segment = st.radio("Market Segment", ["NSE Futures", "MCX Commodity"])
    ticker = st.selectbox("Select Script", st.session_state.wl_nse if segment == "NSE Futures" else st.session_state.wl_mcx)
    
    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

    if user_data["role"] == "admin":
        st.divider()
        with st.expander("🛠️ MASTER ADMIN"):
            # User Management
            new_u = st.text_input("New User ID")
            if st.button("Create"):
                st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "needs_reset": True}
            
            # Funds
            st.divider()
            target_u = st.selectbox("Client", [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"])
            amt = st.number_input("Amount")
            if st.button("Update Funds"):
                st.session_state.user_db[target_u]["balance"] += amt
                st.rerun()
            
            # Ban Scripts
            st.divider()
            b_script = st.text_input("Ban/Unban (eg: CL=F)")
            if st.button("BAN"): st.session_state.banned_scripts.append(b_script)
            if st.button("UNBAN"): st.session_state.banned_scripts.remove(b_script)

# --- TRADE LOGIC ---
def get_data(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, float(df['Close'].iloc[-1])
    return df, 0.0

def validate_trade(symbol, market_type, price, ltp, margin):
    now = datetime.now().time()
    # Market Timing
    if market_type == "NSE Futures":
        if not (time(9,16) <= now <= time(15,30)): return False, "NSE Market Closed"
    else: # MCX
        if not (time(9,1) <= now <= time(23,30)): return False, "MCX Market Closed"
    
    # Rules
    if symbol in st.session_state.banned_scripts: return False, "🚫 Script BANNED"
    if price > (ltp * 1.04) or price < (ltp * 0.96): return False, "4% Limit Rule Violation"
    if user_data["balance"] < margin: return False, "Insufficient Margin"
    
    return True, "Success"

# --- INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Rules"])
data, live_price = get_data(ticker)

with tab1:
    if not data.empty:
        c1, c2 = st.columns([3, 1])
        with c1:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("LTP", f"₹{live_price:,.2f}")
            qty = st.number_input("Qty", min_value=1, value=50)
            order_p = st.number_input("Price", value=live_price)
            margin_needed = (order_p * qty) / 500
            st.write(f"Margin: ₹{margin_needed:,.2f}")
            
            if st.button("BUY / LONG", use_container_width=True, type="primary"):
                ok, msg = validate_trade(ticker, segment, order_p, live_price, margin_needed)
                if ok:
                    st.session_state.user_db[current_user]["balance"] -= margin_needed
                    st.session_state.portfolio.append({
                        "Time": datetime.now(), "Symbol": ticker, "Qty": qty, "Price": order_p, "Margin": margin_needed, "User": current_user
                    })
                    st.success("Order Placed!")
                else: st.error(msg)

with tab2:
    st.subheader("Positions")
    for i, pos in enumerate(st.session_state.portfolio):
        if pos["User"] == current_user:
            pnl = (live_price - pos['Price']) * pos['Qty']
            # 90% Rule
            if pnl <= -(0.9 * pos['Margin']):
                st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.pop(i); st.rerun()
            
            st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
            if st.button(f"SQUARE OFF", key=f"ex_{i}"):
                if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                    st.error("Hold for 2 minutes!")
                else:
                    st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i); st.rerun()

with tab3:
    st.header("📋 Trading Rules")
    st.error("MANDATORY: 2-Minute holding time required for all trades.")
    st.write("• **NSE:** 09:16 - 03:30 | **MCX:** 09:01 - 11:30 PM")
    st.write("• **Execution:** Limit orders within 4% of LTP.")
    st.write("• **MCX Expiry:** Exit Crude/NG 1 day before expiry.")
