import streamlit as st

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kite Lite",
    page_icon="🚀",
    layout="wide"
)

# --- 2. SIDEBAR LOGO & DESIGN ---
# Blue Logo jo aapne bheja tha
# Make sure GitHub par iska naam 'logo.jpg' hi ho
logo_url = "https://raw.githubusercontent.com/Asifnagdade/Kite-Lite/main/logo.jpg"

st.sidebar.image(logo_url, use_container_width=True)

st.sidebar.markdown("""
    <h2 style='color: #4A90E2; font-family: sans-serif; margin-top: -10px; text-align: center;'>Kite Lite</h2>
    """, unsafe_allow_html=True)

# Navigation Radio Buttons
app_mode = st.sidebar.radio("Select Panel", ["Master Control", "Admin Portal"])

st.sidebar.divider()
# Yahan se humne names aur extra text poori tarah hata diya hai.

# --- 3. DYNAMIC FILE LOADER ---
# Is logic se Master aur Admin dono ek hi link par chalenge
if app_mode == "Master Control":
    try:
        # utf-8-sig use kiya hai taaki U+FEFF error na aaye
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
