import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kite Lite", layout="wide")

# --- SIDEBAR DESIGN ---
st.sidebar.title("🪁 Kite Lite") # Ab yahan Control Hub nahi dikhega
app_mode = st.sidebar.radio("Select Panel", ["Master Control", "Admin Portal"])

st.sidebar.divider()
# Hamara naam yahan se hata diya gaya hai

# --- LOGIC TO LOAD FILES (With Encoding Fix) ---
if app_mode == "Master Control":
    try:
        # utf-8-sig use karne se U+FEFF error khatam ho jayega
        with open("master.py", "r", encoding="utf-8-sig") as f:
            code = f.read()
            exec(code)
    except Exception as e:
        st.error(f"Master file loading error: {e}")

elif app_mode == "Admin Portal":
    try:
        with open("admin.py", "r", encoding="utf-8-sig") as f:
            code = f.read()
            exec(code)
    except Exception as e:
        st.error(f"Admin file loading error: {e}")
