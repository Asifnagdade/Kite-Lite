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
if 'orders' not in st.session_state: st.session_state.orders = []

# Watchlists
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
            else: st.error("Invalid Username or Password")
    st.stop()

current_user = st.session_state.logged_in_user
user_data = st.session_state.user_db[current_user]
admin_whatsapp = "96569304925" 

# --- FORCE PASSWORD RESET ---
if user_data.get("needs_reset", False):
    st.warning("🔒 First Time Login: Password reset required.")
    new_p = st.text_input("New Password", type="password")
    conf_p = st.text_input("Confirm Password", type="password")
    if st.button("Set Password"):
        if new_p == conf_p and len(new_p) >= 4:
            st.session_state.user_db[current_user]["pwd"] = new_p
            st.session_state.user_db[current_user]["needs_reset"] = False
            st.success("Success! Please wait...")
            st.rerun()
        else: st.error("Passwords must match and be min 4 characters.")
    st.stop()

# --- SIDEBAR & ADMIN CONTROLS ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"User: **{current_user}** ({user_data['role'].upper()})")
    st.metric("Margin Available", f"₹{user_data['balance']:,.2f}")
    
    if user_data["role"] == "user":
        st.divider()
        msg = urllib.parse.quote(f"Hello Admin, I am {current_user}. Please update my funds.")
        st.markdown(f'<a href="https://wa.me/{admin_whatsapp}?text={msg}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer; font-weight:bold;">💬 Pay-in Request</button></a>', unsafe_allow_html=True)

    segment = st.radio("Market", ["NSE Futures", "MCX Commodity"])
    ticker = st.selectbox("Select Script", st.session_state.wl_nse if segment == "NSE Futures" else st.session_state.wl_mcx)
    if ticker in st.session_state.banned_scripts: st.error("🚫 SCRIPT BANNED")

    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

    if user_data["role"] == "admin":
        st.divider()
        with st.expander("🛠️ MASTER ADMIN CONTROL"):
            # User & Password Reset
            st.subheader("User Management")
            new_u = st.text_input("New User ID")
            if st.button("Create User"):
                if new_u and new_u not in st.session_state.user_db:
                    st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "needs_reset": True}
                    st.success(f"Created {new_u}")
            
            user_list = [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"]
            if user_list:
                res_u = st.selectbox("Select User to Reset", user_list)
                if st.button("Reset PWD to 1234"):
                    st.session_state.user_db[res_u]["pwd"] = "1234"
                    st.session_state.user_db[res_u]["needs_reset"] = True
                    st.warning(f"Reset {res_u}")

            # Funds
            st.divider()
            st.subheader("Balance Control")
            f_u = st.selectbox("Target User", user_list, key="f_sel")
            f_amt = st.number_input("Amount", value=0.0)
            if st.button("Update Balance"):
                st.session_state.user_db[f_u]["balance"] += f_amt
                st.rerun()

            # Ban Control
            st.divider()
            st.subheader("Ban System")
            ban_t = st.text_input("Symbol (eg: CL=F)")
            if st.button("BAN SCRIPT"): st.session_state.banned_scripts.append(ban_t)
            if st.button("UNBAN SCRIPT"): 
                if ban_t in st.session_state.banned_scripts: st.session_state.banned_scripts.remove(ban_t)

# --- TRADE LOGIC ---
def get_data(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, float(df['Close'].iloc[-1])
    return df, 0.0

def validate_entry(symbol, mkt, price, ltp, margin):
    now = datetime.now().time()
    if symbol in st.session_state.banned_scripts: return False, "Script is BANNED."
    if mkt == "NSE Futures":
        if not (time(9,16) <= now <= time(15,30)): return False, "NSE Closed"
    else:
        if not (time(9,1) <= now <= time(23,30)): return False, "MCX Closed"
    if price > (ltp * 1.04) or price < (ltp * 0.96): return False, "4% Limit Violation"
    if user_data["balance"] < margin: return False, "Insufficient Funds"
    return True, "OK"

# --- INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Terminal", "📝 Trade Log", "💼 Portfolio", "📜 Rules"])
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
            order_p = st.number_input("Order Price", value=live_price)
            margin_req = (order_p * qty) / 500
            if st.button("BUY / LONG", use_container_width=True, type="primary"):
                ok, msg = validate_entry(ticker, segment, order_p, live_price, margin_req)
                if ok:
                    st.session_state.user_db[current_user]["balance"] -= margin_req
                    trade = {"Time": datetime.now(), "Symbol": ticker, "Qty": qty, "Price": order_p, "Margin": margin_req, "User": current_user}
                    st.session_state.portfolio.append(trade); st.session_state.orders.append(trade)
                    st.success("Trade Placed!")
                else: st.error(msg)

with tab3:
    st.subheader("Positions")
    for i, pos in enumerate(st.session_state.portfolio):
        if pos["User"] == current_user:
            pnl = (live_price - pos['Price']) * pos['Qty']
            if pnl <= -(0.9 * pos['Margin']): # 90% LOSS RULE
                st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                st.session_state.portfolio.pop(i); st.warning("Auto Square-off (90% Loss)"); st.rerun()
            st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
            if st.button(f"SQUARE OFF {pos['Symbol']}", key=f"ex_{i}"):
                if (datetime.now() - pos["Time"]) < timedelta(minutes=2): # 2-MIN HOLD RULE
                    st.error("Hold for 2 Minutes!")
                else:
                    st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i); st.rerun()

with tab4:
    st.header("📋 Trading Rules")
    st.error("🚫 2-MINUTE HOLDING RULE IS MANDATORY.")
    st.write("• **NSE:** 09:16-03:30 | **MCX:** 09:01-11:30 PM")
    st.write("• **MCX Expiry:** Crude/NG 1 day before, Metals 5 days before.")
    st.write("• **Limits:** Orders within 4% of LTP. Banned scripts block entry.")
    st.write("• **Auto-Exit:** Automatic square-off at 90% capital loss.")
