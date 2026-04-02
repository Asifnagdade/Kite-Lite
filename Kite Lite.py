import streamlit as st
import json
import os

# --- 1. PERMANENT DATABASE (Fixes Login/ID Issue) ---
DB_FILE = "trading_app_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    # Default Admin Access
    return {"users": {"asifnagdade": {"pwd": "Khadija@12", "role": "admin", "bal": 0.0, "first": False}}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if 'db' not in st.session_state: 
    st.session_state.db = load_db()

# --- 2. MOBILE UI STYLING ---
st.set_page_config(page_title="Kite Lite", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #111; color: white; }
    .segment-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .segment-btn { 
        background: #333; padding: 5px 20px; border-radius: 5px; 
        border: 1px solid #444; color: white; cursor: pointer;
    }
    .active-segment { border-bottom: 2px solid orange; color: orange; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIN ENGINE ---
if 'user' not in st.session_state:
    st.title("🛡️ Kite Lite Login")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Login"):
        db = st.session_state.db["users"]
        if u in db and db[u]["pwd"] == p:
            st.session_state.user = u
            st.rerun()
        else: st.error("❌ Invalid ID/Password")
    st.stop()

u_id = st.session_state.user
u_role = st.session_state.db["users"][u_id]["role"]

# --- 4. ADMIN PANEL (ID Creation Access) ---
if u_role == "admin":
    st.sidebar.title("ADMIN CONTROL")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()

    st.header("🛠️ Admin Master Panel")
    tab1, tab2 = st.tabs(["👤 Client Management", "📊 System Audit"])
    
    with tab1:
        st.subheader("Create New User")
        new_u = st.text_input("Username")
        if st.button("Add Client (Default Pwd: 1234)"):
            if new_u and new_u not in st.session_state.db["users"]:
                st.session_state.db["users"][new_u] = {"pwd": "1234", "role": "user", "bal": 0.0, "first": True}
                save_db(st.session_state.db)
                st.success(f"ID '{new_u}' ban gayi aur permanent save ho gayi!")
            else: st.error("Error: ID exists or empty.")

        st.divider()
        st.subheader("Delete User")
        rem_u = st.selectbox("Select User", [k for k in st.session_state.db["users"].keys() if k != "asifnagdade"])
        if st.button("🚫 DELETE PERMANENTLY"):
            del st.session_state.db["users"][rem_u]
            save_db(st.session_state.db)
            st.warning("User deleted from database.")
            st.rerun()

# --- 5. CUSTOMER INTERFACE (NSE & MCX ONLY) ---
else:
    # Sidebar Info
    st.sidebar.title("💎 Kite Lite")
    st.sidebar.write(f"Account: **{u_id}**")
    st.sidebar.write(f"Available Margin: **₹{st.session_state.db['users'][u_id]['bal']}**")
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.rerun()

    # Main Segment Tabs
    st.markdown("### Stocks")
    col1, col2, _ = st.columns([1, 1, 4])
    with col1: st.markdown('<div class="segment-btn active-segment">NSE</div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="segment-btn">MCX</div>', unsafe_allow_html=True)

    # Search Bar
    st.text_input("🔍 Search Script", placeholder="Enter script name...")
    st.info("No Script In Your WatchList")

    # Side Menu Buttons
    st.sidebar.divider()
    st.sidebar.button("📋 Logs")
    st.sidebar.button("📜 Ledger Master")
    
    # Funds Section with WhatsApp (+965 69304925)
    st.sidebar.error("⚠️ NO SCREENSHOT, NO FUNDS")
    if st.sidebar.button("🟢 Click for Pay-in via WhatsApp"):
        st.write("Redirecting to WhatsApp...")
    
    if st.sidebar.button("🔴 Submit Payout Request"):
        st.write("Payout form opening...")
