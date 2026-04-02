import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import calendar
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite", layout="wide", page_icon="📈")

# --- TICKER BASE ---
TICKER_BASE = {
    "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "SBIN": "SBIN.NS",
    "CRUDEOIL": "CL=F", "GOLD": "GC=F", "SILVER": "SI=F", "NATURALGAS": "NG=F"
}

# --- DYNAMIC CONTRACT NAMES (Zerodha Style) ---
def get_contracts():
    now = datetime.now()
    curr_m = now.strftime('%b').upper()
    
    # Expiry Check (Last Thursday for NSE, approx 19th for MCX)
    last_thurs = max(week[calendar.THURSDAY] for week in calendar.monthcalendar(now.year, now.month))
    expiry_date = datetime(now.year, now.month, last_thurs)
    
    # Rule: Show next month ONLY 1 day before current expiry
    show_next = (expiry_date - now).days <= 1
    
    mapping = {}
    for item in TICKER_BASE:
        mapping[f"{item} {curr_m} FUT"] = TICKER_BASE[item]
        if show_next:
            next_m = (now.replace(day=28) + timedelta(days=4)).strftime('%b').upper()
            mapping[f"{item} {next_m} FUT"] = TICKER_BASE[item]
    return mapping

# --- DATABASE & SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []},
        "user1": {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
    }
if 'banned_scripts' not in st.session_state: st.session_state.banned_scripts = [] 
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = [] 

admin_no = "96569304925"

# --- LOGIN SYSTEM ---
if not st.session_state.logged_in_user:
    cols = st.columns([1, 1.2, 1])
    with cols[1]:
        st.title("🔐 Kite Lite Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
                st.session_state.logged_in_user = u
                st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_data = st.session_state.user_db[u_id]

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Account: **{u_id}**")
    st.metric("Balance", f"₹{u_data['balance']:,.2f}")
    
    if u_data["role"] == "user":
        st.divider()
        st.subheader("Fund Requests")
        r_type = st.radio("Type", ["Pay-in", "Payout"])
        r_amt = st.number_input("Amount", min_value=0)
        if st.button("Request via WhatsApp"):
            msg = urllib.parse.quote(f"Admin, I am {u_id}. I need a {r_type} of ₹{r_amt}.")
            st.markdown(f'<a href="https://wa.me/{admin_no}?text={msg}" target="_blank">Send Message</a>', unsafe_allow_html=True)

    st.divider()
    all_contracts = get_contracts()
    disp_ticker = st.selectbox("MarketWatch", list(all_contracts.keys()))
    yf_ticker = all_contracts[disp_ticker]
    
    if disp_ticker in st.session_state.banned_scripts:
        st.error(f"🚫 {disp_ticker} is BANNED")

    if st.button("Logout"):
        st.session_state.logged_in_user = None
        st.rerun()

# --- TABS ---
if u_data["role"] == "admin":
    tabs = st.tabs(["📊 Terminal", "👁️ Admin Monitor (Spy)", "💰 User Funds & ID", "🚫 Ban Control"])
else:
    tabs = st.tabs(["📊 Terminal", "💼 Portfolio (Running)", "📖 Ledger", "📜 Rules"])

# --- TAB 1: TERMINAL ---
with tabs[0]:
    df = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        ltp = float(df['Close'].iloc[-1])
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(disp_ticker)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("LTP", f"₹{ltp:,.2f}")
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1, value=50)
            px = st.number_input("Price", value=ltp)
            
            # --- MARGIN RULE: 500x vs 60x ---
            lev = 500 if "Intraday" in prod else 60
            margin = (px * qty) / lev
            st.write(f"Margin: **₹{margin:,.2f}**")
            
            if st.button("BUY", use_container_width=True, type="primary"):
                # --- VALIDATION RULES ---
                if disp_ticker in st.session_state.banned_scripts: st.error("Script Banned!")
                elif u_data["balance"] < margin: st.error("Low Funds!")
                elif px > (ltp * 1.04) or px < (ltp * 0.96): st.error("LTP Rule: Max 4% range allowed.")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({
                        "User": u_id, "Time": datetime.now(), "Symbol": disp_ticker, 
                        "Qty": qty, "Price": px, "Margin": margin, "Type": prod
                    })
                    st.success("Trade Executed!")

# --- ADMIN SECTION ---
if u_data["role"] == "admin":
    with tabs[1]:
        st.subheader("🕵️ Spy Mode: All Users Running Trades")
        if st.session_state.portfolio:
            st.table(pd.DataFrame(st.session_state.portfolio))
        else: st.info("No active trades.")
    
    with tabs[2]:
        st.subheader("User Management (Funds & ID)")
        u_list = [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"]
        
        # Fund Visibility for Admin
        fund_report = [{"User ID": u, "Balance": f"₹{st.session_state.user_db[u]['balance']:,.2f}"} for u in u_list]
        st.table(pd.DataFrame(fund_report))
        
        st.divider()
        col_id, col_fund = st.columns(2)
        with col_id:
            st.subheader("Create New ID")
            new_u = st.text_input("New User ID")
            if st.button("Create"):
                if new_u and new_u not in st.session_state.user_db:
                    st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
                    st.success("ID Created with ₹0 Balance")
        with col_fund:
            st.subheader("Update Funds")
            target = st.selectbox("Select User", u_list)
            f_type = st.radio("Action", ["Add (Pay-in)", "Remove (Payout)"])
            amt = st.number_input("Amount", key="fund_amt")
            if st.button("Update"):
                val = amt if "Add" in f_type else -amt
                st.session_state.user_db[target]["balance"] += val
                st.session_state.user_db[target]["ledger"].append({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": f_type, "Amount": amt
                })
                st.rerun()

# --- USER SECTION ---
if u_data["role"] == "user":
    with tabs[1]:
        st.subheader("Portfolio (Running Positions)")
        for i, pos in enumerate(st.session_state.portfolio):
            if pos["User"] == u_id:
                pnl = (ltp - pos['Price']) * pos['Qty']
                
                # --- AUTO SQUARE OFF RULE: 90% Loss ---
                if pnl <= -(0.9 * pos['Margin']):
                    st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i)
                    st.warning("Auto Exit: 90% Loss Hit")
                    st.rerun()
                
                st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f} | Margin: ₹{pos['Margin']:,.2f}")
                if st.button(f"Square Off {i}"):
                    # --- 2-MINUTE HOLDING RULE ---
                    if (datetime.now() - pos["Time"]) < timedelta(minutes=2):
                        st.error("Rule: Hold position for at least 2 minutes!")
                    else:
                        st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                        st.session_state.portfolio.pop(i); st.rerun()

    with tabs[2]:
        st.subheader("📖 Ledger (Financial History)")
        if u_data["ledger"]:
            st.table(pd.DataFrame(u_data["ledger"]))
        else: st.info("No transaction history.")

with tabs[-1] if u_data["role"] == "user" else st.empty():
    st.header("📋 Official Trading Rules")
    st.write("1. **Leverage:** Intraday 500x | Delivery 60x.")
    st.write("2. **Holding:** 2-Minute minimum hold time is mandatory.")
    st.write("3. **Auto-Exit:** 90% capital loss results in automatic square-off.")
    st.write("4. **Limits:** Orders must be within 4% of LTP.")
    st.write("5. **New Contracts:** Show only 1 day before expiry.")
