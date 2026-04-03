import streamlit as st

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Kite Lite",
    page_icon="🚀",
    layout="wide"
)

# --- 2. SIDEBAR LOGO & DESIGN ---
# Aapki image ka exact naam jo GitHub par hai
logo_url = "https://raw.githubusercontent.com/Asifnagdade/Kite-Lite/main/5aa27d17-020c-4911-809e-6d01d3eb0271.jpg"

st.sidebar.image(logo_url, use_container_width=True)

st.sidebar.markdown("""
    <h2 style='color: #4A90E2; font-family: sans-serif; margin-top: -10px; text-align: center;'>Kite Lite</h2>
    """, unsafe_allow_html=True)

# Navigation
app_mode = st.sidebar.radio("Select Panel", ["Master Control", "Admin Portal"])
st.sidebar.divider()

# --- 3. DYNAMIC FILE LOADER ---
# Yahan humne file names ko Small Letters mein kar diya hai jo aapke GitHub se match kare
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
