import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIG ---
st.set_page_config(page_title="Kite Lite Pro", layout="wide")

# --- 2. PERMANENT DATABASE (FIXED) ---
# Ye logic ensure karta hai ki IDs refresh hone par gayab na hon
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "asifnagdade": {"pwd": "Khadija@12", "role": "admin", "balance": 0.0, "ledger": [], "first_login": False}
    }

# Baaki data initialization
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'order_history' not in st.session_state: st.session_state.order_history = []
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None

# --- 3. LOGIN ENGINE (SMOOTH SYNC) ---
if not st.session_state.logged_in_user:
    st.title("🔐 Kite Lite Login")
    u_in = st.text_input("Username").strip()
    p_in = st.text_input("Password", type="password").strip()
    
    if st.button("Login"):
        # Direct check from the live session state
        if u_in in st.session_state.user_db:
            if st.session_state.user_db[u_in]["pwd"] == p_in:
                st.session_state.logged_in_user = u_in
                st.rerun()
            else:
                st.error("❌ Galat Password!")
        else:
            st.error(f"❌ ID '{u_in}' nahi mili! Admin se create karwayein.")
    st.stop()

# Get User Info
u_id = st.session_state.logged_in_user
u_role = st.session_state.user_db[u_id]["role"]

# --- 4. ADMIN MASTER PANEL (FULL DELETE ACCESS) ---
if u_role == "admin":
    st.header("🛠️ Admin Master Control")
    t1, t2, t3, t4 = st.tabs(["👤 ID Management", "💰 Ledger Control", "📋 Live Trades", "📑 Trade History"])
    
    with t1: # Nayi ID banane ka full access
        st.subheader("Add New Client ID")
        new_u = st.text_input("New ID Name")
        if st.button("✅ Create ID Now"):
            if new_u and new_u not in st.session_state.user_db:
                # Direct update to session_state
                st.session_state.user_db[new_u] = {"pwd": "1234", "role": "user", "balance": 0.0, "ledger": [], "first_login": True}
                st.success(f"ID '{new_u}' Created! Default Pass: 1234")
            else: st.error("ID pehle se hai ya naam khali hai.")

        st.divider()
        st.subheader("Delete or Reset ID")
        m_id = st.selectbox("Select ID", [k for k in st.session_state.user_db.keys() if k != "asifnagdade"])
        if st.button("🚫 DELETE ID PERMANENTLY"):
            del st.session_state.user_db[m_id]
            st.warning("User Deleted!")
            st.rerun()

    with t3: # Live Position Deletion
        st.subheader("Live Trade Monitor (Delete Live)")
        if st.session_state.portfolio:
            for i, p in enumerate(st.session_state.portfolio):
                col = st.columns([4, 1])
                col[0].write(f"User: {p['User']} | {p['Sym']} | Qty: {p['Qty']}")
                if col[1].button(f"Delete Trade {i}", key=f"lt_{i}"):
                    st.session_state.portfolio.pop(i); st.rerun()
        else: st.info("No Live Trades.")

    with t4: # Permanent History Deletion
        st.subheader("History Deletion (Delete Records)")
        if st.session_state.order_history:
            for i, h in enumerate(st.session_state.order_history):
                col = st.columns([4, 1])
                col[0].write(f"{h['User']} | {h['Sym']} | {h['Time']}")
                if col[1].button(f"🗑️ Delete Record {i}", key=f"th_{i}"):
                    st.session_state.order_history.pop(i); st.rerun()

# --- 5. CLIENT SECTION ---
else:
    # First Login Password Change
    if st.session_state.user_db[u_id].get("first_login", True):
        st.title("Welcome! Change Your Password")
        np = st.text_input("New Password", type="password")
        if st.button("Save & Start"):
            st.session_state.user_db[u_id]["pwd"] = np
            st.session_state.user_db[u_id]["first_login"] = False
            st.success("Updated! Now you can trade.")
            st.rerun()
        st.stop()

    # Funds Section (WhatsApp: +965 69304925)
    st.sidebar.write(f"Balance: ₹{st.session_state.user_db[u_id]['balance']:,.2f}")
    if st.sidebar.button("Logout"): st.session_state.logged_in_user = None; st.rerun()

    st.subheader("Funds Management")
    st.error("⚠️ DISCLAIMER: WITHOUT SCREENSHOT AND PAYMENT PROOF, WE WILL NOT ADD FUNDS.")
    
    val = st.number_input("Amount", step=100)
    wa_url = f"https://wa.me/96569304925?text=Payin%20Request:%20{val}%20User:%20{u_id}"
    if st.button("Pay-in via WhatsApp"):
        st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_url}">', unsafe_allow_html=True)
