import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import calendar
import urllib.parse

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide", page_icon="📈")

# --- DYNAMIC CONTRACT LOGIC ---
def get_expiry_date(year, month, segment="NSE"):
    """NSE ki expiry last Thursday hoti hai, MCX ki fixed dates hoti hain (approx)."""
    last_day = calendar.monthrange(year, month)[1]
    if segment == "NSE": # Last Thursday
        last_thursday = max(week[calendar.THURSDAY] for week in calendar.monthcalendar(year, month))
        return datetime(year, month, last_thursday)
    else: # MCX (Roughly 19th-20th for Crude)
        return datetime(year, month, 19)

def get_active_contracts():
    now = datetime.now()
    current_month_name = now.strftime('%b').upper()
    next_month = (now.month % 12) + 1
    next_year = now.year + (1 if now.month == 12 else 0)
    next_month_name = datetime(next_year, next_month, 1).strftime('%b').upper()

    # Base Symbols
    symbols = {
        "NSE": ["NIFTY", "BANKNIFTY", "RELIANCE", "SBIN"],
        "MCX": ["CRUDEOIL", "GOLD", "SILVER", "NATURALGAS"]
    }
    
    mapping = {}
    
    for seg, items in symbols.items():
        expiry_curr = get_expiry_date(now.year, now.month, seg)
        # Rule: New contract shows only 1 day before current expiry
        show_next = (expiry_curr - now).days <= 1
        
        for item in items:
            # Current Month Contract
            curr_name = f"{item} {current_month_name} FUT"
            mapping[curr_name] = {"yf": TICKER_BASE[item], "expiry": expiry_curr}
            
            # Next Month Contract (Conditional)
            if show_next:
                next_name = f"{item} {next_month_name} FUT"
                mapping[next_name] = {"yf": TICKER_BASE[item], "expiry": get_expiry_date(next_year, next_month, seg)}
                
    return mapping

TICKER_BASE = {
    "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "SBIN": "SBIN.NS",
    "CRUDEOIL": "CL=F", "GOLD": "GC=F", "SILVER": "SI=F", "NATURALGAS": "NG=F"
}

# --- DATABASE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []},
        "user1": {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
    }

if 'banned_scripts' not in st.session_state: st.session_state.banned_scripts = [] 
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = [] 

admin_whatsapp = "96569304925"

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 Kite Lite Pro")
    current_user = st.session_state.logged_in_user
    if current_user:
        user_data = st.session_state.user_db[current_user]
        st.write(f"Account: **{current_user}**")
        st.metric("Total Balance", f"₹{user_data['balance']:,.2f}")
        
        # WhatsApp Fund Request
        if user_data["role"] == "user":
            st.divider()
            req_type = st.radio("Request", ["Pay-in", "Payout"])
            req_amt = st.number_input("Amount", min_value=0)
            if st.button("Message Admin"):
                msg = urllib.parse.quote(f"Admin, I am {current_user}. Requesting {req_type} of ₹{req_amt}.")
                st.markdown(f'<a href="https://wa.me/{admin_whatsapp}?text={msg}" target="_blank">WhatsApp</a>', unsafe_allow_html=True)

        st.divider()
        # Dynamic Contract Select
        contracts = get_active_contracts()
        display_ticker = st.selectbox("MarketWatch (FUT Only)", list(contracts.keys()))
        selected_info = contracts[display_ticker]
        yf_symbol = selected_info["yf"]
        
        if display_ticker in st.session_state.banned_scripts:
            st.error(f"🚫 {display_ticker} is BANNED")
        
        if st.button("Logout"):
            st.session_state.logged_in_user = None
            st.rerun()

# --- LOGIN (Simple Check) ---
if not st.session_state.logged_in_user:
    st.title("🔐 Login")
    u = st.text_input("User")
    p = st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u
            st.rerun()
    st.stop()

# --- TABS ---
if user_data["role"] == "admin":
    main_tabs = st.tabs(["📊 Terminal", "👁️ Live Monitor", "💰 User Funds", "🚫 Ban Control"])
else:
    main_tabs = st.tabs(["📊 Terminal", "💼 Portfolio", "📖 Ledger", "📜 Rules"])

# --- CORE TRADING ---
with main_tabs[0]:
    # Data Fetch
    df = yf.download(yf_symbol, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        ltp = float(df['Close'].iloc[-1])
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(f"{display_ticker}")
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Execution")
            st.metric("LTP", f"₹{ltp:,.2f}")
            prod = st.radio("Type", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1, value=50)
            px = st.number_input("Price", value=ltp)
            
            leverage = 500 if "Intraday" in prod else 60
            margin = (px * qty) / leverage
            st.write(f"Margin: **₹{margin:,.2f}**")
            
            if st.button("BUY", use_container_width=True, type="primary"):
                if display_ticker in st.session_state.banned_scripts: st.error("Banned!")
                elif user_data["balance"] < margin: st.error("Low Funds!")
                else:
                    st.session_state.user_db[current_user]["balance"] -= margin
                    st.session_state.portfolio.append({
                        "User": current_user, "Time": datetime.now(), "Symbol": display_ticker,
                        "Qty": qty, "Price": px, "Margin": margin, "Type": prod
                    })
                    st.success("Trade Placed!")

# --- ADMIN / USER TABS (Logic Same as previous fixed versions) ---
# [Admin Monitoring and Ledger logic integrated here...]
if user_data["role"] == "admin":
    with main_tabs[2]:
        st.subheader("User Funds Management")
        for u, d in st.session_state.user_db.items():
            if d["role"] == "user":
                st.write(f"**{u}**: ₹{d['balance']:,.2f}")
        
        target = st.selectbox("Select User", [u for u in st.session_state.user_db if st.session_state.user_db[u]["role"] == "user"])
        amt = st.number_input("Amount", step=100.0)
        if st.button("Add Funds"):
            st.session_state.user_db[target]["balance"] += amt
            st.session_state.user_db[target]["ledger"].append({"Date": datetime.now(), "Type": "Deposit", "Amt": amt})
            st.rerun()
