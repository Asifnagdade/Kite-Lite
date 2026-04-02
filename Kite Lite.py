import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- MASTER DATABASE INITIALIZATION ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []},
        "user1": {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
    }

if 'banned_scripts' not in st.session_state: st.session_state.banned_scripts = [] 
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = [] # Active Trades
if 'trade_history' not in st.session_state: st.session_state.trade_history = [] # Closed Trades

# Admin Settings
admin_whatsapp = "96569304925"

# --- LOGIN & SECURITY ---
if not st.session_state.logged_in_user:
    cols = st.columns([1, 1.2, 1])
    with cols[1]:
        st.title("🔐 Kite Lite Pro Login")
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

# Force Password Reset
if user_data.get("needs_reset", False):
    new_p = st.text_input("Security Alert: Set New Password", type="password")
    if st.button("Update Password"):
        st.session_state.user_db[current_user]["pwd"] = new_p
        st.session_state.user_db[current_user]["needs_reset"] = False
        st.rerun()
    st.stop()

# --- SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.title("💎 Kite Lite Pro")
    st.write(f"Logged in: **{current_user}**")
    st.metric("Total Margin", f"₹{user_data['balance']:,.2f}")
    
    # Funds Request (WhatsApp Link)
    if user_data["role"] == "user":
        st.divider()
        st.subheader("Fund Requests")
        req_type = st.radio("Type", ["Pay-in", "Payout"])
        req_amt = st.number_input("Amount", min_value=0)
        if st.button("Send Request to Admin"):
            msg = urllib.parse.quote(f"Admin, I am {current_user}. I am requesting a {req_type} of ₹{req_amt}.")
            st.markdown(f'<a href="https://wa.me/{admin_whatsapp}?text={msg}" target="_blank">Redirect to WhatsApp</a>', unsafe_allow_html=True)

    st.divider()
    segment = st.radio("Market", ["NSE Futures", "MCX Commodity"])
    watch_list = ["^NSEI", "^NSEBANK", "RELIANCE.NS", "SBIN.NS", "GC=F", "CL=F", "SI=F", "NG=F"]
    ticker = st.selectbox("Select Script", watch_list)
    
    if st.button("Log Out"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- HELPER FUNCTIONS ---
def get_live_data(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, float(df['Close'].iloc[-1])
    return pd.DataFrame(), 0.0

# --- MAIN NAVIGATION TABS ---
# Admin sees Monitoring, User sees Terminal
if user_data["role"] == "admin":
    main_tabs = st.tabs(["📊 Terminal", "👁️ Admin Monitor", "👤 User Funds", "🚫 Ban List"])
else:
    main_tabs = st.tabs(["📊 Terminal", "💼 Portfolio", "📖 Ledger", "📜 Rules"])

# --- TAB 1: TERMINAL (Common for both) ---
with main_tabs[0]:
    data, ltp = get_live_data(ticker)
    if not data.empty:
        c1, c2 = st.columns([3, 1])
        with c1:
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Order Window")
            st.metric("LTP", f"₹{ltp:,.2f}")
            order_type = st.radio("Product", ["Intraday (500x)", "Delivery (1x)"])
            qty = st.number_input("Quantity", min_value=1, value=1)
            limit_p = st.number_input("Price", value=ltp)
            
            leverage = 500 if "Intraday" in order_type else 1
            margin_req = (limit_p * qty) / leverage
            st.write(f"Margin Required: **₹{margin_req:,.2f}**")
            
            if st.button("BUY / LONG", use_container_width=True, type="primary"):
                # Basic Rules Check
                if ticker in st.session_state.banned_scripts: st.error("Banned Script!")
                elif user_data["balance"] < margin_req: st.error("Insufficient Funds!")
                elif limit_p > (ltp * 1.04) or limit_p < (ltp * 0.96): st.error("LTP Rule 4% Violation")
                else:
                    st.session_state.user_db[current_user]["balance"] -= margin_req
                    st.session_state.portfolio.append({
                        "User": current_user, "Time": datetime.now(), "Symbol": ticker,
                        "Qty": qty, "Price": limit_p, "Margin": margin_req, "Type": order_type
                    })
                    st.success("Order Placed Successfully!")

# --- USER SPECIFIC TABS ---
if user_data["role"] == "user":
    # PORTFOLIO TAB
    with main_tabs[1]:
        st.subheader("🏃 Running Positions")
        user_active = [p for p in st.session_state.portfolio if p["User"] == current_user]
        if user_active:
            for i, pos in enumerate(st.session_state.portfolio):
                if pos["User"] == current_user:
                    pnl = (ltp - pos['Price']) * pos['Qty']
                    st.write(f"**{pos['Symbol']}** | Qty: {pos['Qty']} | P&L: :green[₹{pnl:,.2f}]" if pnl >=0 else f"**{pos['Symbol']}** | Qty: {pos['Qty']} | P&L: :red[₹{pnl:,.2f}]")
                    if st.button(f"Square Off {i}", key=f"sq_{i}"):
                        if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                            st.error("Hold for 2 minutes!")
                        else:
                            st.session_state.user_db[current_user]["balance"] += (pos['Margin'] + pnl)
                            st.session_state.trade_history.append({**pos, "ExitPrice": ltp, "PnL": pnl, "ExitTime": datetime.now()})
                            st.session_state.portfolio.pop(i); st.rerun()
        else: st.info("No active trades.")

    # LEDGER TAB
    with main_tabs[2]:
        st.subheader("📊 Financial Ledger")
        st.write(f"Current Available Balance: **₹{user_data['balance']:,.2f}**")
        if user_data["ledger"]:
            df_ledger = pd.DataFrame(user_data["ledger"])
            st.table(df_ledger)
        else: st.info("No transaction history yet.")

# --- ADMIN SPECIFIC TABS ---
if user_data["role"] == "admin":
    # MONITOR TAB
    with main_tabs[1]:
        st.subheader("🕵️ Live Monitoring (All Users)")
        if st.session_state.portfolio:
            df_monitor = pd.DataFrame(st.session_state.portfolio)
            st.dataframe(df_monitor, use_container_width=True)
        else: st.info("No users are currently trading.")
        
        st.divider()
        st.subheader("📜 Master Trade History")
        if st.session_state.trade_history:
            st.dataframe(pd.DataFrame(st.session_state.trade_history), use_container_width=True)

    # USER FUNDS TAB
    with main_tabs[2]:
        st.subheader("Manage User Balance & ID")
        new_uid = st.text_input("New User ID")
        if st.button("Create ID"):
            st.session_state.user_db[new_uid] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
            st.success(f"ID {new_uid} created with ₹0 balance.")
        
        st.divider()
        target_u = st.selectbox("Select User", [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"])
        f_type = st.radio("Action", ["Deposit (Pay-in)", "Withdraw (Payout)"])
        f_amt = st.number_input("Amount", key="admin_amt")
        if st.button("Confirm Transaction"):
            final_amt = f_amt if f_type == "Deposit (Pay-in)" else -f_amt
            st.session_state.user_db[target_u]["balance"] += final_amt
            st.session_state.user_db[target_u]["ledger"].append({
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Type": f_type, "Amount": f_amt, "Status": "Success"
            })
            st.success(f"Successfully updated {target_u}'s balance.")

    # BAN LIST TAB
    with main_tabs[3]:
        st.subheader("Market Ban Control")
        ban_sym = st.text_input("Enter Symbol to Ban")
        if st.button("Ban Now"): st.session_state.banned_scripts.append(ban_sym)
        st.write("Currently Banned:", st.session_state.banned_scripts)

with main_tabs[-1] if user_data["role"] == "user" else st.empty():
    st.header("📋 Official Trading Rules")
    st.warning("All trades must be held for 2 minutes.")
    st.write("NSE: 09:16-15:30 | MCX: 09:01-23:30")
