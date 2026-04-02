import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- 1. PERMANENT DATABASE ENGINE ---
DB_FILE = "kite_replica_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {
        "users": {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "bal": 100000.0}},
        "portfolio": [], "history": []
    }

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- 2. ZERODHA STYLING (KITE BLUE & WHITE) ---
st.set_page_config(page_title="Kite Replica", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #fff; color: #444; }
    .header { background: #fff; border-bottom: 1px solid #eee; padding: 10px 20px; display: flex; justify-content: space-between; }
    .watchlist-item { border-bottom: 1px solid #eee; padding: 12px; display: flex; justify-content: space-between; cursor: pointer; }
    .watchlist-item:hover { background: #fcfcfc; }
    .buy-btn { background-color: #4184f3; color: white; border: none; border-radius: 3px; padding: 5px 15px; }
    .sell-btn { background-color: #ff5722; color: white; border: none; border-radius: 3px; padding: 5px 15px; }
    .price-up { color: #4caf50; }
    .price-down { color: #df514c; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIN SYSTEM (STABLE) ---
if 'user' not in st.session_state:
    st.markdown("<h2 style='text-align: center; color: #ff5722;'>Kite</h2>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("User ID (Client ID)").strip()
        p = st.text_input("Password", type="password").strip()
        if st.button("Login", use_container_width=True):
            db = st.session_state.db["users"]
            if u in db and db[u]["pwd"] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid credentials")
    st.stop()

u_id = st.session_state.user
u_role = st.session_state.db["users"][u_id]["role"]

# --- 4. ADMIN PANEL (FULL CONTROL & DELETE) ---
if u_role == "admin":
    st.sidebar.title("Kite Admin")
    menu = st.sidebar.radio("Menu", ["User Management", "Live Trades", "Master History", "Logout"])
    
    if menu == "Logout":
        del st.session_state.user; st.rerun()

    if menu == "User Management":
        st.subheader("Manage Client IDs")
        c1, c2 = st.columns(2)
        with c1:
            new_u = st.text_input("New Client ID")
            if st.button("Create ID"):
                if new_u and new_u not in st.session_state.db["users"]:
                    st.session_state.db["users"][new_u] = {"pwd": "1234", "role": "user", "bal": 0.0}
                    save_db(st.session_state.db)
                    st.success(f"ID {new_u} Created (Saved to File)")
                else: st.error("ID exists or empty")
        with c2:
            rem_u = st.selectbox("Select User to Delete", [k for k in st.session_state.db["users"].keys() if k != "asifnagdade"])
            if st.button("🗑️ DELETE ID PERMANENTLY"):
                del st.session_state.db["users"][rem_u]
                save_db(st.session_state.db); st.warning("User Deleted"); st.rerun()

    elif menu == "Live Trades":
        st.subheader("Force Delete Live Positions")
        # Logic to list and delete items from st.session_state.db["portfolio"]

# --- 5. CLIENT REPLICA (ZERODHA INTERFACE) ---
else:
    # Top Bar
    st.markdown(f"""
        <div class="header">
            <div style="color: #ff5722; font-weight: bold; font-size: 20px;">KITE</div>
            <div>Dashboard | Orders | <b>Holdings</b> | Positions | Funds</div>
            <div style="color: #666;">ID: {u_id} | <span style="color: #4184f3;">₹{st.session_state.db['users'][u_id]['bal']}</span></div>
        </div>
    """, unsafe_allow_html=True)

    col_watch, col_trade = st.columns([1, 2])

    with col_watch:
        st.markdown("### Marketwatch")
        st.text_input("🔍 Search eg: NIFTY APR FUT", label_visibility="collapsed")
        
        # Example Future Contracts (CFT Dabba Style)
        scripts = [
            {"name": "CRUDEOIL APR FUT", "price": "7124.00", "change": "+0.45%"},
            {"name": "GOLD JUNE FUT", "price": "72450.00", "change": "-0.12%"},
            {"name": "NIFTY APR FUT", "price": "22540.10", "change": "+0.85%"}
        ]
        
        for s in scripts:
            st.markdown(f"""
                <div class="watchlist-item">
                    <span><b>{s['name']}</b></span>
                    <span class="price-up">{s['price']} ({s['change']})</span>
                </div>
            """, unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button(f"BUY", key=f"b_{s['name']}"): st.session_state.trade_type = "BUY"
            if c2.button(f"SELL", key=f"s_{s['name']}"): st.session_state.trade_type = "SELL"

    with col_trade:
        st.markdown("### Order Window (Futures Only)")
        st.info("Trading Rule: Only Future Contracts | Custom Quantity Enabled")
        
        # Order Form
        with st.form("trade_form"):
            st.write("**NIFTY APR FUT**")
            qty = st.number_input("Qty (Units)", min_value=1, value=50)
            price_type = st.radio("Type", ["Market", "Limit"], horizontal=True)
            
            # Zerodha Style Buttons
            if st.form_submit_button("PLACE ORDER", use_container_width=True):
                st.success(f"Order Placed: {qty} Units @ Market")

    # Side Menu / Funds
    with st.sidebar:
        st.error("⚠️ NO SCREENSHOT, NO FUNDS (+965 69304925)")
        st.button("📜 Ledger")
        st.button("📊 Trade Logs")
        if st.button("Logout"): del st.session_state.user; st.rerun()
