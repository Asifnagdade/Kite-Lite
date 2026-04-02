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

if 'banned_scripts' not in st.session_state: st.session_state.banned_scripts = [] 
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = []

# Watchlists (NSE Futures & MCX only)
if 'wl_nse' not in st.session_state: st.session_state.wl_nse = ["^NSEI", "^NSEBANK", "RELIANCE.NS", "SBIN.NS", "TCS.NS"]
if 'wl_mcx' not in st.session_state: st.session_state.wl_mcx = ["GC=F", "CL=F", "SI=F", "NG=F"]

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

# YOUR WHATSAPP NUMBER UPDATED HERE
admin_whatsapp = "96569304925" 

# Force Password Reset for New Users
if user_data.get("needs_reset", False):
    st.warning("🔒 Pehli baar login: Security ke liye Password badalna zaroori hai.")
    new_p = st.text_input("Naya Password", type="password")
    conf_p = st.text_input("Confirm Naya Password", type="password")
    if st.button("Update & Login"):
        if new_p == conf_p and len(new_p) >= 4:
            st.session_state.user_db[current_user]["pwd"] = new_p
            st.session_state.user_db[current_user]["needs_reset"] = False
            st.success("Password Updated!")
            st.rerun()
        else: st.error("Password match nahi kar rahe ya bahut chote hain.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{current_user}** ({user_data['role'].upper()})")
    st.metric("Available Balance", f"₹{user_data['balance']:,.2f}")
    
    # WHATSAPP REDIRECT (Only for Clients)
    if user_data["role"] == "user":
        st.divider()
        msg = f"Hello Admin, I am {current_user}. I want to request a Pay-in/Fund Update for my account."
        encoded_msg = urllib.parse.quote(msg)
        st.markdown(f'''
            <a href="https://wa.me/{admin_whatsapp}?text={encoded_msg}" target="_blank">
                <button style="width:100%; background-color:#25D366; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:14px;">
                    💬 Request Pay-in / Funds
                </button>
            </a>
            ''', unsafe_allow_html=True)
        st.divider()

    segment = st.radio("Market Segment", ["NSE Futures", "MCX Commodity"])
    ticker = st.selectbox("Select Script", st.session_state.wl_nse if segment == "NSE Futures" else st.session_state.wl_mcx)
    
    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

    # --- ADMIN MASTER CONTROLS ---
    if user_data["role"] == "admin":
        st.divider()
        with st.expander("🛠️ MASTER ADMIN CONTROL"):
            # Create/Reset
            st.subheader("User Management")
            new_u = st.text_input("New User ID")
            if st.button("Create Account"):
                if new_u and new_u not in st.session_state.user_db:
                    st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "needs_reset": True}
                    st.success("User Created (PWD: 1234)")
            
            # Reset Password Option
            st_user_list = [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"]
            if st_user_list:
                res_u = st.selectbox("Reset Password for:", st_user_list)
                if st.button("Reset to 1234"):
                    st.session_state.user_db[res_u]["pwd"] = "1234"
                    st.session_state.user_db[res_u]["needs_reset"] = True
                    st.warning("Password Reset Done.")

            # Funds Management
            st.divider()
            st.subheader("Balance Management")
            fund_u = st.selectbox("Target Client", st_user_list, key="fund_sel")
            amt = st.number_input("Amount (+ or -)", value=0.0)
            if st.button("Update Funds"):
                st.session_state.user_db[fund_u]["balance"] += amt
                st.success("Balance Updated!")
                st.rerun()

# --- DATA & TRADE LOGIC ---
def get_live_data(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, float(df['Close'].iloc[-1])
    return df, 0.0

def validate_trade(symbol, mkt_type, price, ltp, margin):
    now = datetime.now().time()
    # Market Timing Check
    if mkt_type == "NSE Futures":
        if not (time(9,16) <= now <= time(15,30)): return False, "NSE Market Closed (09:16-15:30)"
    else: # MCX
        if not (time(9,1) <= now <= time(23,30)): return False, "MCX Market Closed (09:01-23:30)"
    
    # 4% Limit Check
    if price > (ltp * 1.04) or price < (ltp * 0.96): return False, "Limit order max 4% distance from LTP allowed."
    # Banned Script
    if symbol in st.session_state.banned_scripts: return False, "Script is BANNED by Admin."
    # Balance
    if user_data["balance"] < margin: return False, "Insufficient Funds."
    
    return True, "Valid"

# --- MAIN INTERFACE ---
tab1, tab2, tab3 = st.tabs(["📊 Terminal", "💼 Portfolio", "📜 Rules"])
data, live_price = get_live_data(ticker)

with tab1:
    if not data.empty:
        c1, c2 = st.columns([3, 1])
        with c1:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("LTP", f"₹{live_price:,.2f}")
            qty = st.number_input("Quantity", min_value=1, value=50)
            order_p = st.number_input("Limit Price", value=live_price)
            margin_req = (order_p * qty) / 500 # Default leverage
            st.write(f"Margin: ₹{margin_req:,.2f}")
            
            if st.button("PLACE BUY ORDER", use_container_width=True, type="primary"):
                ok, msg = validate_trade(ticker, segment, order_p, live_price, margin_req)
                if ok:
                    st.session_state.user_db[current_user]["balance"] -= margin_req
                    st.session_state.portfolio.append({
                        "Time": datetime.now(), "Symbol": ticker, "Qty": qty, 
                        "Price": order_p, "Margin": margin_req, "User": current_user
                    })
                    st.success("Trade Executed!")
                else: st.error(msg)
    else: st.error("Market data fetching error.")

with tab2:
    st.subheader("Active Positions")
    user_pos = [p for p in st.session_state.portfolio if p["User"] == current_user]
    if user_pos:
        for i, pos in enumerate(st.session_state.portfolio):
            if pos["User"] == current_user:
                pnl = (live_price - pos['Price']) * pos['Qty']
                # 90% Loss Square-Off
                if pnl <= -(0.9 * pos['Margin']):
                    st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i); st.rerun()
                
                st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f} | Entry: ₹{pos['Price']}")
                # 2-MINUTE HOLDING RULE
                if st.button(f"SQUARE OFF {pos['Symbol']}", key=f"ex_{i}"):
                    wait = datetime.now() - pos["Time"]
                    if wait < timedelta(minutes=2):
                        st.error(f"Rule: Wait {int(120 - wait.total_seconds())}s more to exit.")
                    else:
                        st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                        st.session_state.portfolio.pop(i); st.rerun()
    else: st.info("No open positions.")

with tab3:
    st.header("📋 Trading Rules & Regulations")
    st.error("🚫 2-MINUTE HOLDING RULE: No trade can be exited before 2 minutes of entry.")
    st.write("• NSE Hours: 09:16 AM - 03:30 PM | MCX Hours: 09:01 AM - 11:30 PM.")
    st.write("• All limit orders must be within 4% range of LTP.")
    st.write("• Auto Square-off occurs at 90% loss of the invested margin.")
    st.write("• BTST/STBT is strictly not allowed.")
