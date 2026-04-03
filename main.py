import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Kite Lite",
    page_icon="🚀",
    layout="wide"
)

# --- LOGO & TITLE DESIGN ---
# Is code se aapka upload kiya hua blue logo sidebar mein top par dikhega
st.sidebar.image("https://raw.githubusercontent.com/Asifnagdade/Kite-Lite/main/logo.jpg", width=200)

st.sidebar.markdown("""
    <h2 style='color: #184ba3; font-family: sans-serif; margin-top: -10px;'>Kite Lite</h2>
    """, unsafe_allow_html=True)

# Navigation
app_mode = st.sidebar.radio("Select Panel", ["Master Control", "Admin Portal"])
st.sidebar.divider()

# --- LOGIC TO LOAD FILES ---
if app_mode == "Master Control":
    try:
        with open("master.py", "r", encoding="utf-8-sig") as f:
            exec(f.read())
    except Exception as e:
        st.error(f"Master file loading error: {e}")

elif app_mode == "Admin Portal":
    try:
        with open("admin.py", "r", encoding="utf-8-sig") as f:
            exec(f.read())
    except Exception as e:
        st.error(f"Admin file loading error: {e}")
