import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & PERMANENT STATE ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide")

# Database ko refresh hone se bachane ke liye strict check
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 2. LOGIN SYSTEM (NO ERROR LOGIC) ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    # .strip() use kiya hai taaki extra spaces se error na aaye
    u_in = st.text_input("Username").strip()
    p_in = st.text_input("Password", type="password").strip()
    
    if st.button("Login"):
        if u_in in st.session_state.user_db:
            if st.session_state.user_db[u_in]["pwd"] == p_in:
                st.session_state.logged_in_user = u_in
                st.rerun()
            else:
                st.error("❌ Galat Password! Admin se check karein.")
        else:
            st.error(f"❌ User '{u_in}' nahi mila! Admin ko ID banane bole.")
    st.stop()

u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 3. ADMIN MASTER PANEL (FULL DELETE CONTROL) ---
if u_role == "admin":
    st.header("🛠️ Admin Master Control")
    t1, t2, t3, t4 = st.tabs(["👤 ID Management", "💰 Ledger", "📋 Live Positions", "📑 History Audit"])
    
    with t1: # ID Creation & Reset
        st.subheader("Create New Client")
        new_u = st.text_input("New Username (Case Sensitive)")
        if st.button("✅ Create ID Now"):
            if new_u and new_u not in st.session_state.user_db:
                st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                st.success(f"ID '{new_u}' ban gayi hai! Password: 1234")
            else: st.error("ID pehle se hai ya naam khali hai.")

        st.divider()
        st.subheader("Manage IDs")
        m_id = st.selectbox("Select ID to Action", [k for k in st.session_state.user_db.keys() if k != "asifnagdade"])
        if st.button("Reset Password to 1234"):
            st.session_state.user_db[m_id]["pwd"] = "1234"
            st.session_state.user_db[m_id]["first_login"] = True
            st.info("Password Reset Done.")
        if st.button("🗑️ DELETE ID PERMANENTLY"):
            del st.session_state.user_db[m_id]
            st.warning("User Deleted!")
            st.rerun()

    with t3: # Permanent Trade Deletion
        st.subheader("Live Trade Monitor")
        if st.session_state.portfolio:
            for i, p in enumerate(st.session_state.portfolio):
                c = st.columns([4, 1])
                c[0].write(f"{p['User']} | {p['Sym']} | Qty: {p['Qty']}")
                if c[1].button(f"Delete Trade {i}", key=f"lt_{i}"):
                    st.session_state.portfolio.pop(i); st.rerun()
        else: st.info("No Live Trades.")

# --- 4. CLIENT INTERFACE (WATCHLIST & FUNDS) ---
else:
    # First Login Password Change
    if st.session_state.user_db[u_id].get("first_login", True):
        st.title("Welcome! Change Your Password")
        np = st.text_input("New Password", type="password")
        if st.button("Save & Start Trading"):
            st.session_state.user_db[u_id]["pwd"] = np
            st.session_state.user_db[u_id]["first_login"] = False
            st.success("Password Updated!")
            st.rerun()
        st.stop()

    # Funds with WhatsApp
    st.sidebar.write(f"Wallet: ₹{st.session_state.user_db[u_id]['balance']}")
    if st.sidebar.button("Logout"): st.session_state.logged_in_user = None; st.rerun()

    st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
    # Pay-in WhatsApp Button (+965 69304925)
    f_val = st.number_input("Amount", step=100)
    wa_url = f"https://wa.me/96569304925?text=Payin%20Request:%20{f_val}%20User:%20{u_id}"
    if st.button("Pay-in via WhatsApp"):
        st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_url}">', unsafe_allow_html=True)
