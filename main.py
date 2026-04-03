import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="Trading Control Hub", layout="wide")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 Control Hub")
app_mode = st.sidebar.radio("Select Panel", ["Master Control", "Admin Portal"])

st.sidebar.divider()
st.sidebar.info("Asif & Affan's Trading System")

# --- LOGIC TO LOAD FILES (Using your Small Names) ---
if app_mode == "Master Control":
    try:
        # Ab filenames small hain
        exec(open("master.py").read())
    except Exception as e:
        st.error(f"Master file loading error: {e}")

elif app_mode == "Admin Portal":
    try:
        exec(open("admin.py").read())
    except Exception as e:
        st.error(f"Admin file loading error: {e}")
