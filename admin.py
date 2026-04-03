import streamlit as st
import pandas as pd
import os

st.title("🛡️ Admin Portal")

if 'a_auth' not in st.session_state: st.session_state.a_auth = False
if not st.session_state.a_auth:
    u = st.text_input("Admin ID")
    p = st.text_input("Password", type="password")
    if st.button("Login Admin"):
        df = pd.read_csv("users.csv", dtype=str)
        if not df[(df['username']==u) & (df['password']==p) & (df['role']=='admin')].empty:
            st.session_state.a_auth = True; st.session_state.admin_user = u; st.rerun()
        else: st.error("Invalid Login")
else:
    st.header(f"Admin: {st.session_state.admin_user}")
    tab1, tab2 = st.tabs(["📈 Client Management", "📊 Signal/Order Logs"])
    with tab1:
        st.button("Add New Trader/User")
        st.write("Manage Limits & Margin for Users")
    if st.button("Logout"):
        st.session_state.a_auth = False; st.rerun()
