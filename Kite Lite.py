import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite", layout="wide", page_icon="📈")

# --- MASTER DATA (Strictly from your list) ---
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

# --- SESSION STATE ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": []},
        "user1": {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": []}
    }
if 'nse_watchlist' not in st.session_state: st.session_state.nse_watchlist = ["NIFTY 50"]
if 'mcx_watchlist' not in st.session_state: st.session_state.mcx_watchlist = ["CRUDEOIL"]
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'portfolio' not in st.session_state: st.session_state.portfolio = [] 

# --- EXPIRY LOGIC ---
def get_exp_names():
    now = datetime.now()
    curr_m = now.strftime('%b').upper()
    next_m = (now.replace(day=28) + timedelta(days=4)).strftime('%b').upper()
    last_thurs = max(week[calendar.THURSDAY] for week in calendar.monthcalendar(now.year, now.month))
    show_next = (datetime(now.year, now.month, last_thurs) - now).days <= 1
    return curr_m, next_m, show_next

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

# --- SIDEBAR: SEGMENT-WISE ADD ---
curr_m, next_m, show_next = get_exp_names()

with st.sidebar:
    st.title("💎 Kite Lite")
    st.metric("Balance", f"₹{u_data['balance']:,.2f}")
    
    st.divider()
    st.subheader("🔍 Add to Watchlist")
    add_seg = st.selectbox("Select Segment", ["NSE", "MCX"])
    base_options = list(MASTER_DATA[add_seg].keys())
    
    search_list = [f"{b} {curr_m} FUT" for b in base_options]
    if show_next: search_list += [f"{b} {next_m} FUT" for b in base_options]
            
    to_add = st.selectbox("Search Contract", search_list)
    if st.button("Add"):
        if add_seg == "NSE":
            if to_add not in st.session_state.nse_watchlist: st.session_state.nse_watchlist.append(to_add)
        else:
            if to_add not in st.session_state.mcx_watchlist: st.session_state.mcx_watchlist.append(to_add)
        st.success(f"Added to {add_seg} List")

# --- TERMINAL TABS ---
t1, t2, t3, t4 = st.tabs(["📊 Terminal", "💼 Portfolio", "📖 Ledger", "📜 Rules"])

with t1:
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        sel_nse = st.selectbox("📈 NSE Watchlist", st.session_state.nse_watchlist)
    with col_w2:
        sel_mcx = st.selectbox("🧱 MCX Watchlist", st.session_state.mcx_watchlist)
    
    final_sel = st.radio("Active Script", [sel_nse, sel_mcx], horizontal=True)
    
    # Identify Data
    base_name = final_sel.split(' ')[0]
    is_mcx = any(x in final_sel for x in MASTER_DATA["MCX"].keys())
    yf_ticker = MASTER_DATA["MCX"].get(base_name) if is_mcx else MASTER_DATA["NSE"].get(base_name)

    if yf_ticker:
        with st.spinner("Fetching Live Price..."):
            df = yf.download(yf_ticker, period="1d", interval="1m", progress=False)
            
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                
                # Live USDINR for MCX
                usd_val = 87.80 # Fallback
                if is_mcx:
                    try: 
                        u_df = yf.download("USDINR=X", period="1d", interval="1m", progress=False)
                        usd_val = u_df['Close'].iloc[-1]
                    except: pass
                
                ltp = round(df['Close'].iloc[-1] * usd_val if is_mcx else df['Close'].iloc[-1], 2)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                    fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, title=final_sel)
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.metric("LTP", f"₹{ltp:,.2f}")
                    prod = st.radio("Product", ["Intraday (500x)", "Delivery (60x)"])
                    qty = st.number_input("Qty", min_value=1, value=1)
                    px = st.number_input("Price", value=ltp)
                    
                    lev = 500 if "Intraday" in prod else 60
                    margin = (px * qty) / lev
                    st.write(f"Margin: **₹{margin:,.2f}**")
                    
                    if st.button("BUY", use_container_width=True, type="primary"):
                        if u_data["balance"] < margin: st.error("Low Funds!")
                        elif px > (ltp * 1.04) or px < (ltp * 0.96): st.error("Price Range (4%)")
                        else:
                            st.session_state.user_db[u_id]["balance"] -= margin
                            st.session_state.portfolio.append({"User": u_id, "Time": datetime.now(), "Symbol": final_sel, "Qty": qty, "Price": px, "Margin": margin, "Type": prod})
                            st.success("Trade Placed!")
            else:
                st.error("Market data currently unavailable for this script. Try NIFTY or CRUDE.")

# --- RULES ---
with t4:
    st.markdown("""
    ### Kite Lite Rules:
    * **NSE Watchlist:** Stocks added here stay in the NSE list.
    * **MCX Watchlist:** Commodities stay in the MCX list.
    * **Leverage:** Intraday 500x | Delivery 60x.
    * **Expiry:** New contracts appear only 1 day before expiry.
    * **Holding:** Minimum 2-minute hold required before exit.
    """)
