import streamlit as st
import pandas as pd
import os

def load_db():
    if os.path.exists("users.csv"): return pd.read_csv("users.csv", dtype=str)
    return pd.DataFrame([["asifnagdade","1234","master"]], columns=["username","password","role"])

st.title("🔑 Master Control Panel")

if 'm_auth' not in st.session_state: st.session_state.m_auth = False
if not st.session_state.m_auth:
    with st.form("m_login"):
        u = st.text_input("Master ID")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u == "asifnagdade" and p == "1234":
                st.session_state.m_auth = True
                st.rerun()
            else: st.error("Wrong ID")
else:
    t1, t2, t3 = st.tabs(["💰 Total AUM", "👥 Create Admin", "⚙️ Global Settings"])
    with t1:
        st.metric("Total Platform Fund", "₹ 1.25 Cr", "+₹ 5.2L Today")
        st.write("Admin Breakdown:")
        st.dataframe(pd.DataFrame({"Admin": ["Admin_Shaalan", "Admin_Chetan"], "Funds": ["50L", "30L"], "PNL": ["+20k", "-5k"]}))
    with t2:
        with st.form("new_admin"):
            name = st.text_input("Partner Name")
            pw = st.text_input("Set Password", "1234")
            if st.form_submit_button("Add Admin"):
                df = load_db()
                new = pd.DataFrame([[f"admin_{name.lower()}", pw, "admin"]], columns=df.columns)
                pd.concat([df, new]).to_csv("users.csv", index=False)
                st.success(f"ID Created: admin_{name.lower()}")
    if st.button("Logout"):
        st.session_state.m_auth = False
        st.rerun()
