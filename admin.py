import streamlit as st
import pandas as pd
import os

# --- ADMIN LOGIN PAGE ---
st.title("🛡️ Admin Portal")

# User database load karne ka function
def load_users():
    if os.path.exists("users.csv"):
        return pd.read_csv("users.csv")
    return pd.DataFrame(columns=["username", "password", "role"])

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    with st.form("admin_login"):
        u_id = st.text_input("Admin ID")
        u_pass = st.text_input("Password", type="password")
        btn = st.form_submit_button("Login to Admin Portal")

        if btn:
            df = load_users()
            # Yahan hum check kar rahe hain ki ID database mein hai aur role 'admin' hai
            user_match = df[(df['username'] == u_id) & (df['password'] == str(u_pass))]
            
            if not user_match.empty:
                role = user_match.iloc[0]['role']
                if role == 'admin':
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_user = u_id
                    st.rerun()
                else:
                    st.error("Access Denied: You do not have Admin privileges.")
            else:
                st.error("Invalid Admin ID or Password.")
else:
    st.success(f"Welcome to Admin Dashboard, {st.session_state.admin_user}")
    if st.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()
    
    # --- YAHAN SE AAPKA ADMIN KA KAAM SHURU HOGA ---
    st.write("Manage your traders and signals here.")
