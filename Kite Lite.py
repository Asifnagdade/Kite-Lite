import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Terminal", layout="wide", page_icon="💎")

# --- MASTER DATABASE & SESSION INITIALIZATION ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0},
        "user1": {"pwd": "user123", "role": "user", "balance": 10000.0}
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
user_role = st.session_state.user_db[current_user]["role"]
whatsapp_number = "919000000000" # <-- Change to your number

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite Terminal")
    st.write(f"Account: **{current_user}** ({user_role.upper()})")
    user_bal = st.session_state.user_db[current_user]["balance"]
    st.metric("Available Balance", f"₹{user_bal:,.2f}")
    
    if user_role == "user":
        st.divider()
        st.subheader("Funds Management")
        msg = urllib.parse.quote(f"Hello Admin, I ({current_user}) request a fund update.")
        st.markdown(f'''<a href="https://wa.me/{whatsapp_number}?text={msg}" target="_blank"><button style="width:100%; border-radius:5px; background-color:#25D366; color:white; border:none; padding:10px; cursor:pointer;">Request Pay-in / Payout</button></a>''', unsafe_allow_html=True)

    st.divider()
    ticker = st.selectbox("Select Script", st.session_state.wl1)
    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- MASTER ADMIN PANEL ---
if user_role == "admin":
    with st.expander("🛠️ MASTER CONTROL PANEL"):
        st.subheader("Manage Client Funds")
        clients = [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"]
        if clients:
            target = st.selectbox("Select Client", clients)
            amt = st.number_input("Add/Subtract Funds", value=0.0)
            if st.button("Update Virtual Balance"):
                st.session_state.user_db[target]["balance"] += amt
                st.success(f"Updated {target}'s balance.")
                st.rerun()
        else: st.info("No client accounts found.")

# --- DATA FETCHING (FIXED ERROR) ---
def get_live_data(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        # Handling MultiIndex Columns if they exist
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, float(df['Close'].iloc[-1])
    return df, 0.0

# --- TRADE VALIDATION & RULES ---
def validate_trade(market, margin_required):
    now = datetime.now().time()
    # Timings [cite: 6, 41]
    if market == "NSE":
        if not (time(9,16) <= now <= time(15,30)): return False, "NSE Market Closed (09:16 - 15:30)" [cite: 6]
        if now >= time(15,25): return False, "New entries restricted in final 5 mins."
    else: 
        if not (time(9,1) <= now <= time(23,30)): return False, "MCX Market Closed (09:01 - 23:30)" [cite: 41]
        if now >= time(23,25): return False, "New entries restricted in final 5 mins."
    
    if st.session_state.user_db[current_user]["balance"] < margin_required:
        return False, "Insufficient Balance for this trade."
    return True, "Valid"

# --- MAIN INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Terminal", "📝 Trade Log", "💼 Portfolio", "📜 Rules"])

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
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Quantity", min_value=1, value=50)
            mult = 500 if "Intraday" in prod else 60
            margin = (live_price * qty) / mult
            st.write(f"Margin Required: ₹{margin:,.2f}")
            
            market_type = "MCX" if ticker in ["GC=F", "CL=F", "SI=F", "NG=F"] else "NSE"
            if st.button("PLACE ORDER", use_container_width=True, type="primary"):
                ok, msg = validate_trade(market_type, margin)
                if ok:
                    st.session_state.user_db[current_user]["balance"] -= margin
                    trade_info = {"Time": datetime.now().strftime("%H:%M:%S"), "Symbol": ticker, "Qty": qty, "Price": live_price, "Margin": margin, "User": current_user}
                    st.session_state.orders.append(trade_info)
                    st.session_state.portfolio.append(trade_info)
                    st.success("Trade Successful!")
                else: st.error(msg)
    else:
        st.error("Error fetching market data. Please check connection.")

with tab3:
    st.subheader("Active Positions")
    if st.session_state.portfolio:
        for i, pos in enumerate(st.session_state.portfolio):
            if pos["User"] == current_user:
                pnl = (live_price - pos['Price']) * pos['Qty']
                if pnl <= -(0.9 * pos['Margin']): # 90% Rule [cite: 21, 48]
                    st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i)
                    st.warning(f"Position {pos['Symbol']} Auto-Squared Off (90% Loss).")
                    st.rerun()
                st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
    else: st.info("No active positions.")

with tab4:
    st.header("📋 Compulsory Rules & Regulations")
    c_a, c_b = st.columns(2)
    with c_a:
        st.subheader("NSE Futures")
        st.write("• Trading Hours: 09:16 to 03:30 [cite: 6]")
        st.write("• Pending orders deleted after market close [cite: 7]")
        st.write("• Limit orders within 4% of LTP [cite: 11]")
        st.write("• Auto-square off at 90% loss of capital [cite: 21]")
    with c_b:
        st.subheader("MCX Futures")
        st.write("• Trading Hours: 09:01 to 23:30 [cite: 41]")
        st.write("• Exit Crude/NG 1 day before expiry [cite: 56]")
        st.write("• Exit Bullions/Metals 5 days before expiry [cite: 57]")
        st.write("• Auto-square off at 90% loss of capital [cite: 48]")
