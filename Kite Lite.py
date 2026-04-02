import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite", layout="wide", page_icon="📈")

# --- MASTER DATA & EXPIRY LOGIC ---
MASTER_DATA = {
    "NSE": {
        "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", 
        "SBIN": "SBIN.NS", "TATA MOTORS": "TATAMOTORS.NS"
    },
    "MCX": {
        "GOLD": "GC=F", "SILVER": "SI=F", "COPPER": "HG=F", "CRUDEOIL": "CL=F",
        "GOLDM": "GOLDM.NS", "NATURALGAS": "NG=F", "ZINC": "ZINC1!S",
        "SILVERM": "SIL=F", "SILVERMIC": "SILMIC.NS", "CRUDEOILM": "QM=F",
        "ZINCMINI": "ZINC-MINI.NS", "NATGASMINI": "QG=F"
    }
}

def get_contract_details():
    now = datetime.now()
    # Maan lo Crude ki expiry 20th ko hai aur baki ki last Thursday
    # Hum yahan dynamic months calculate kar rahe hain
    curr_m_name = now.strftime('%b').upper()
    next_m_date = (now.replace(day=28) + timedelta(days=4))
    next_m_name = next_m_date.strftime('%b').upper()

    # Expiry Rules (Simplified for Logic)
    # NSE: Last Thursday | MCX: Approx 20th
    last_thurs = max(week[calendar.THURSDAY] for week in calendar.monthcalendar(now.year, now.month))
    curr_expiry = datetime(now.year, now.month, last_thurs)
    
    # Rule: Check if today is 1 day before expiry
    show_next_gen = (curr_expiry - now).days <= 1
    
    return curr_m_name, next_m_name, show_next_gen

# --- DATABASE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []},
        "user1": {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
    }
if 'user_watchlist' not in st.session_state: st.session_state.user_watchlist = ["NIFTY 50", "CRUDEOIL"]
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = [] 

# --- LOGIN ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u, p = st.text_input("User"), st.text_input("Pass", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u; st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_data = st.session_state.user_db[u_id]

# --- SIDEBAR & DYNAMIC SEARCH ---
curr_m, next_m, show_next = get_contract_details()

with st.sidebar:
    st.title("💎 Kite Lite")
    st.write(f"Balance: **₹{u_data['balance']:,.2f}**")
    
    st.divider()
    st.subheader("🔍 Add Scripts")
    seg = st.selectbox("Segment", ["MCX", "NSE"])
    base_options = list(MASTER_DATA[seg].keys())
    
    # Expiry-based Search Options
    final_search_list = []
    for b in base_options:
        final_search_list.append(f"{b} {curr_m} FUT")
        if show_next: # Sirf 1 din pehle dikhega
            final_search_list.append(f"{b} {next_m} FUT")
            
    script_to_add = st.selectbox("Search Contract", final_search_list)
    
    if st.button("Add to Watchlist"):
        if script_to_add not in st.session_state.user_watchlist:
            st.session_state.user_watchlist.append(script_to_add); st.rerun()

    st.divider()
    selected_disp = st.selectbox("MarketWatch", st.session_state.user_watchlist)
    selected_base = selected_disp.split(' ')[0]
    yf_sym = MASTER_DATA["NSE"].get(selected_base) or MASTER_DATA["MCX"].get(selected_base)

# --- TERMINAL ---
t1, t2, t3, t4 = st.tabs(["📊 Terminal", "💼 Portfolio", "📖 Ledger", "📜 Rules"])

with t1:
    # Fetch Data with INR Scaling
    df = yf.download(yf_sym, period="1d", interval="1m", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Real-time Price Conversion (MCX India Fix)
        usd_inr = yf.download("USDINR=X", period="1d", interval="1m", progress=False)['Close'].iloc[-1]
        ltp = round(float(df['Close'].iloc[-1]) * usd_inr if "NSE" not in selected_disp else float(df['Close'].iloc[-1]), 2)
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader(f"{selected_disp}")
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.metric("LTP", f"₹{ltp:,.2f}")
            prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
            qty = st.number_input("Qty", min_value=1, value=1)
            px = st.number_input("Price", value=ltp)
            
            # 60x Delivery vs 500x Intraday
            lev = 500 if "Intraday" in prod else 60
            margin = (px * qty) / lev
            st.write(f"Margin: **₹{margin:,.2f}**")
            
            if st.button("PLACE ORDER", use_container_width=True, type="primary"):
                if u_data["balance"] < margin: st.error("Low Funds!")
                elif px > (ltp * 1.04) or px < (ltp * 0.96): st.error("4% Range Violation!")
                else:
                    st.session_state.user_db[u_id]["balance"] -= margin
                    st.session_state.portfolio.append({"User": u_id, "Time": datetime.now(), "Symbol": selected_disp, "Qty": qty, "Price": px, "Margin": margin, "Type": prod})
                    st.success("Trade Placed!")

# --- PORTFOLIO & RULES ---
with t2:
    for i, pos in enumerate(st.session_state.portfolio):
        if pos["User"] == u_id:
            pnl = (ltp - pos['Price']) * pos['Qty']
            st.write(f"**{pos['Symbol']}** | P&L: ₹{pnl:,.2f}")
            if st.button(f"Exit {i}"):
                if (datetime.now() - pos["Time"]) < timedelta(minutes=2): st.error("Hold 2 Mins!")
                else:
                    st.session_state.user_db[u_id]["balance"] += (pos['Margin'] + pnl)
                    st.session_state.portfolio.pop(i); st.rerun()

with t4:
    st.info("Rules: 500x Intraday, 60x Delivery, 2-Min Holding, 4% Limit, 1-Day Before Expiry New Contract.")
