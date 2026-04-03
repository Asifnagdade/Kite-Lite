import streamlit as st
import pandas as pd
import os

# --- DATABASE LOGIC FOR TRADERS ---
def load_traders():
    if os.path.exists("traders.csv"):
        return pd.read_csv("traders.csv", dtype=str)
    return pd.DataFrame(columns=["trader_id", "password", "parent_admin", "margin"])

def save_trader(t_id, t_pass, admin_name, margin):
    df = load_traders()
    new_t = pd.DataFrame([[t_id, t_pass, admin_name, margin]], columns=df.columns)
    pd.concat([df, new_t], ignore_index=True).to_csv("traders.csv", index=False)

st.title("🛡️ Admin Portal")

# --- LOGIN LOGIC ---
if 'a_auth' not in st.session_state: st.session_state.a_auth = False
if not st.session_state.a_auth:
    u = st.text_input("Admin ID")
    p = st.text_input("Password", type="password")
    if st.button("Login Admin"):
        if os.path.exists("users.csv"):
            df = pd.read_csv("users.csv", dtype=str)
            check = df[(df['username']==u) & (df['password']==p) & (df['role']=='admin')]
            if not check.empty:
                st.session_state.a_auth = True
                st.session_state.admin_user = u
                st.rerun()
            else: st.error("Invalid Admin ID or Password")
        else: st.error("System Error: users.csv not found")
else:
    st.sidebar.success(f"Logged in: {st.session_state.admin_user}")
    
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "📊 Live Signals", "💸 Reports"])

    with tab1:
        st.subheader("Add New Trader")
        with st.form("add_trader_form"):
            t_name = st.text_input("Trader Name")
            t_pass = st.text_input("Set Trader Password", "1234")
            t_margin = st.number_input("Assign Margin (Limit)", min_value=0, value=10000)
            
            if st.form_submit_button("Create Trader Account"):
                if t_name:
                    trader_full_id = f"user_{t_name.lower().strip()}"
                    save_trader(trader_full_id, t_pass, st.session_state.admin_user, str(t_margin))
                    st.success(f"✅ Trader Created! ID: {trader_full_id}")
                    st.rerun()
                else: st.error("Please enter a name")

        st.divider()
        st.subheader("Your Active Traders")
        all_traders = load_traders()
        # Sirf is Admin ke traders dikhao
        my_traders = all_traders[all_traders['parent_admin'] == st.session_state.admin_user]
        st.dataframe(my_traders, use_container_width=True)

    if st.sidebar.button("Logout"):
        st.session_state.a_auth = False
        st.rerun()
