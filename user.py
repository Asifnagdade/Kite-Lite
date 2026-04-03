import streamlit as st

st.title("💹 Kite Lite Trading Terminal")

# Sidebar Rules for User
st.sidebar.info("📌 **Trading Rules:**\n- Min Holding: 2 Mins\n- Futures Only\n- Custom Qty Allowed")

# --- SCRIPTS LIST ---
nse_futures = ["NIFTY-FUT", "BANKNIFTY-FUT", "RELIANCE-FUT", "HDFCBANK-FUT", "INFY-FUT", "TCS-FUT", "SBIN-FUT"]
mcx_futures = ["CRUDEOIL-FUT", "GOLD-FUT", "SILVER-FUT", "NATURALGAS-FUT", "COPPER-FUT"]

col_watch, col_trade = st.columns([1, 2])

with col_watch:
    st.subheader("Watchlist")
    market = st.radio("Market", ["NSE FUT", "MCX"])
    scripts = nse_futures if market == "NSE FUT" else mcx_futures
    selected_script = st.selectbox("Select Script to Trade", scripts)
    st.metric(selected_script, "LTP: ₹ 22,450", "+0.45%")

with col_trade:
    st.subheader(f"Trade {selected_script}")
    with st.container(border=True):
        qty = st.number_input("Customize Quantity (Lots)", min_value=1, step=1)
        price_type = st.radio("Order Type", ["Market", "Limit"], horizontal=True)
        
        col_b, col_s = st.columns(2)
        if col_b.button("BUY / LONG", type="primary", use_container_width=True):
            st.toast(f"Order Placed: BUY {qty} qty of {selected_script}")
        if col_s.button("SELL / SHORT", type="secondary", use_container_width=True):
            st.toast(f"Order Placed: SELL {qty} qty of {selected_script}")

    st.divider()
    st.subheader("Open Positions")
    st.warning("Note: Trades closed within 120 seconds will be automatically reversed.")
    st.table({"Script": [selected_script], "Qty": [qty], "Entry": [22400], "Time": ["14:30:05"], "PNL": ["+₹ 1,200"]})
