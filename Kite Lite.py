import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite", layout="wide", page_icon="📈")

# --- MASTER DATA (As per your Screenshot list) ---
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

# --- EXPIRY LOGIC (1-Day Rule) ---
def get_expiry_options():
    now = datetime.now()
    curr_m = now.strftime('%b').upper()
    next_m = (now.replace(day=28) + timedelta(days=4)).strftime('%b').upper()
    
    # Last Thursday of month logic for expiry
    last_day = calendar.monthrange(now.year, now.month)[1]
    last_thurs = max(week[calendar.THURSDAY] for week in calendar.monthcalendar(now.year, now.month))
    expiry_date = datetime(now.year, now.month, last_thurs)
    
    show_next = (expiry_date - now).days <= 1
    return curr_m, next_m, show_next

# --- SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []},
        "user1": {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "needs_reset": True}
    }
if 'user_watchlist' not in st.session_state: st.session_state.user_watchlist = ["NIFTY 50"]
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

# --- SIDEBAR & SEARCH ---
curr_m, next_m, show_next = get_expiry_options()

with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Balance", f"₹{u_data['balance']:,.2f}")
    
    st.divider()
    st.subheader("🔍 Add Scripts")
    seg = st.selectbox("Segment", ["MCX", "NSE"])
    base_options = list(MASTER_DATA[seg].keys())
    
    search_list = [f"{b} {curr_m} FUT" for b in base_options]
    if show_next:
        search_list += [f"{b} {next_m} FUT" for b in base_options]
            
    script_to_add = st.selectbox("Search Contract", search_list)
    if st.button("Add to Watchlist"):
        if script_to_add not in st.session_state.user_watchlist:
            st.session_state.user_watchlist.append(script_to_add); st.rerun()

    st.divider()
    selected_disp = st.selectbox("MarketWatch", st.session_state.user_watchlist if st.session_state.user_watchlist else ["NIFTY 50"])
    
    # Error Proofing the symbol extraction
    selected_base = selected_disp.split(' ')[0] if ' ' in selected_disp else selected_disp
    yf_sym = MASTER_DATA["NSE"].get(selected_base) or MASTER_DATA["MCX"].get(selected_base) or "^NSEI"

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["📊 Terminal", "💼 Portfolio", "📖 Ledger", "📜 Rules"])

with t1:
    if yf_sym:
        try:
            df = yf.download(yf_sym, period="1d", interval="1m", progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                
                # MCX INR Conversion Logic
                usd_rate = 87.50 # Fallback rate
                try:
                    usd_df = yf.download("USDINR=X", period="1d", interval="1m", progress=False)
                    if not usd_df.empty: usd_rate = usd_df['Close'].iloc[-1]
                except: pass
                
                raw_ltp = float(df['Close'].iloc[-1])
                ltp = round(raw_ltp * usd_rate if seg == "MCX" else raw_ltp, 2)
                
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
                    
                    lev = 500 if "Intraday" in prod else 60
                    margin = (px * qty) / lev
                    st.write(f"Margin: **₹{margin:,.2f}**")
                    
                    if st.button("PLACE ORDER", use_container_width=True, type="primary"):
                        if u_data["balance"] < margin: st.error("Low Funds!")
                        elif px > (ltp * 1.04) or px < (ltp * 0.96): st.error("Price Limit (4%)")
                        else:
                            st.session_state.user_db[u_id]["balance"] -= margin
                            st.session_state.portfolio.append({"User": u_id, "Time": datetime.now(), "Symbol": selected_disp, "Qty": qty, "Price": px, "Margin": margin, "Type": prod})
                            st.success("Trade Placed!")
            else:
                st.error("Market Data not available for this ticker.")
        except Exception as e:
            st.error(f"System Error: Connection issue with Market Data.")
    else:
        st.warning("Please select a valid script from Watchlist.")

# Rules section with 60x Delivery Highlight
with t4:
    st.info("Delivery Leverage: 60x | Intraday Leverage: 500x | New contract appears 1 day before expiry.")
