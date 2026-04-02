import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & DATA PERSISTENCE ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide")

# Initializing the database if not present
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 2. LOGIN SYSTEM (STRICT CHECK) ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u_in = st.text_input("Username").strip()
    p_in = st.text_input("Password", type="password").strip()
    
    if st.button("Login"):
        # Direct check against the session state database
        if u_in in st.session_state.user_db:
            if st.session_state.user_db[u_in]["pwd"] == p_in:
                st.session_state.logged_in_user = u_in
                st.rerun()
            else:
                st.error("❌ Galat Password! Admin se sahi password lein.")
        else:
            st.error(f"❌ User '{u_in}' nahi mila! Admin ko ID banane bole.")
    st.stop()

# Get current user data
u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 3. ADMIN PANEL (FULL DELETE & MGMT) ---
if u_role == "admin":
    st.header("🛠️ Admin Master Control")
    tabs = st.tabs(["👤 ID Management", "💰 Ledger", "📋 Live Trades", "📑 History Audit"])
    
    with tabs[0]: # ID Creation & Deletion
        st.subheader("Create New Client")
        new_u = st.text_input("New Username")
        if st.button("✅ Create ID Now"):
            if new_u and new_u not in st.session_state.user_db:
                st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                st.success(f"ID '{new_u}' created! Password: 1234")
            else: st.error("ID exists or name empty.")

        st.divider()
        st.subheader("ID Actions")
        m_id = st.selectbox("Select ID", [k for k in st.session_state.user_db.keys() if k != "asifnagdade"])
        c1, c2 = st.columns(2)
        if c1.button("Reset to 1234"):
            st.session_state.user_db[m_id]["pwd"] = "1234"
            st.session_state.user_db[m_id]["first_login"] = True
            st.info("Reset Done.")
        if c2.button("🗑️ DELETE ID PERMANENTLY"):
            del st.session_state.user_db[m_id]
            st.warning("User Deleted!")
            st.rerun()

    with tabs[2]: # Delete Live Trades
        st.subheader("Live Portfolio Monitor")
        if st.session_state.portfolio:
            for i, p in enumerate(st.session_state.portfolio):
                col = st.columns([4, 1])
                col[0].write(f"User: {p['User']} | {p['Sym']} | Qty: {p['Qty']}")
                if col[1].button(f"Delete Trade {i}", key=f"lt_{i}"):
                    st.session_state.portfolio.pop(i); st.rerun()
        else: st.info("No Live Trades.")

    with tabs[3]: # History Deletion
        st.subheader("Trade History (Permanent Delete)")
        if st.session_state.order_history:
            for i, h in enumerate(st.session_state.order_history):
                col = st.columns([4, 1])
                col[0].write(f"{h['User']} | {h['Sym']} | {h['Time']}")
                if col[1].button(f"🗑️ Delete Record {i}", key=f"th_{i}"):
                    st.session_state.order_history.pop(i); st.rerun()

# --- 4. CLIENT INTERFACE ---
else:
    # First Login Password Force
    if st.session_state.user_db[u_id].get("first_login", True):
        st.title("Change Your Password")
        np = st.text_input("New Password", type="password")
        if st.button("Save & Start Trading"):
            st.session_state.user_db[u_id]["pwd"] = np
            st.session_state.user_db[u_id]["first_login"] = False
            st.success("Updated! Refreshing...")
            st.rerun()
        st.stop()

    # Funds with WhatsApp Redirect
    st.sidebar.write(f"Balance: ₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    if st.sidebar.button("Logout"): st.session_state.logged_in_user = None; st.rerun()

    st.subheader("Funds Management")
    st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
    
    val = st.number_input("Enter Amount", step=100)
    # WhatsApp Pay-in (Kuwait Number: +965 69304925)
    wa_url = f"https://wa.me/96569304925?text=Payin%20Request:%20{val}%20User:%20{u_id}"
    if st.button("Pay-in via WhatsApp"):
        st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_url}">', unsafe_allow_html=True)
    
    if st.button("Payout Request"):
        if val > st.session_state.user_db[u_id]["balance"] or val <= 0:
            st.error("Insufficient Balance!")
        else:
            wa_out = f"https://wa.me/96569304925?text=Payout%20Request:%20{val}%20User:%20{u_id}"
            st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_out}">', unsafe_allow_html=True)
