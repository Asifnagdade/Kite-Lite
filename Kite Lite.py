import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. SESSION STATE (Admin, Portfolio, History) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 2. LOGIN CHECK ---
if not st.session_state.logged_in_user:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in st.session_state.user_db and st.session_state.user_db[u]["pwd"] == p:
            st.session_state.logged_in_user = u
            st.rerun()
    st.stop()

u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 3. ADMIN PANEL (With Delete Powers) ---
if u_role == "admin":
    st.header("🛠️ Admin Master Control")
    t1, t2, t3 = st.tabs(["👤 User Management", "📋 Live Positions", "📑 Permanent Trade History"])

    with t1:
        st.subheader("ID Controls")
        target_u = st.selectbox("Select User", [k for k, v in st.session_state.user_db.items() if v['role'] == 'user'])
        if st.button("Delete This User Permanently"):
            del st.session_state.user_db[target_u]
            st.warning(f"User {target_u} has been deleted.")
            st.rerun()

    with t2:
        st.subheader("Force Close / Delete Live Trades")
        if st.session_state.portfolio:
            for i, pos in enumerate(st.session_state.portfolio):
                col1, col2 = st.columns([4, 1])
                col1.write(f"**User:** {pos['User']} | **Script:** {pos['Sym']} | **Qty:** {pos['Qty']}")
                if col2.button(f"Delete Trade {i}", key=f"del_pos_{i}"):
                    st.session_state.portfolio.pop(i)
                    st.success("Live Trade Deleted!")
                    st.rerun()
        else: st.info("No Live Positions.")

    with t3:
        st.subheader("Permanent History Deletion")
        if st.session_state.order_history:
            # Display history with a delete button for each record
            history_df = pd.DataFrame(st.session_state.order_history)
            st.write("Full Trade Records:")
            for i, order in enumerate(st.session_state.order_history):
                c1, c2 = st.columns([4, 1])
                c1.write(f"ID: {i} | {order['User']} | {order['Sym']} | {order['Time']}")
                if c2.button(f"🗑️ Permanent Delete {i}", key=f"his_del_{i}"):
                    st.session_state.order_history.pop(i)
                    st.warning(f"Trade Record {i} Deleted Permanently.")
                    st.rerun()
        else: st.info("History is empty.")

else:
    # CLIENT SECTION
    st.write(f"Welcome {u_id}. Start Trading.")
    # (Existing Terminal & Funds logic here)
