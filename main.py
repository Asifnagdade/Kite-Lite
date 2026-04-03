import streamlit as st

# Sidebar for Navigation
st.sidebar.title("Navigation Hub")
app_mode = st.sidebar.selectbox("Choose Panel", ["Master Control", "Admin Portal"])

if app_mode == "Master Control":
    # Master file ka content yahan load hoga
    exec(open("master.py").read())
elif app_mode == "Admin Portal":
    # Admin file ka content yahan load hoga
    exec(open("admin.py").read())