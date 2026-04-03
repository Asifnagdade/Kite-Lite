import streamlit as st

st.set_page_config(page_title="Kite Lite | Trading Terminal", page_icon="🚀", layout="wide")

# --- SIDEBAR LOGO ---
logo_url = "https://raw.githubusercontent.com/Asifnagdade/Kite-Lite/main/5aa27d17-020c-4911-809e-6d01d3eb0271.jpg"
st.sidebar.image(logo_url, use_container_width=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #4A90E2;'>Kite Lite</h2>", unsafe_allow_html=True)

# Navigation Menu
menu = ["User Terminal", "Admin Portal", "Master Control"]
choice = st.sidebar.selectbox("Access Level", menu)

# Strict Rules Display in Sidebar
st.sidebar.divider()
st.sidebar.warning("⚠️ **Dabba Trading Rules (CFT):**\n1. Only Future Trading allowed.\n2. 2-Min Scalping NOT allowed.\n3. Trades closed before 2 mins will be VOID.\n4. NSE & MCX Scripts only.")

def load_page(file_name):
    try:
        with open(file_name, "r", encoding="utf-8-sig") as f:
            exec(f.read(), globals())
    except Exception as e:
        st.error(f"Error loading {file_name}: {e}")

if choice == "Master Control":
    load_page("master.py")
elif choice == "Admin Portal":
    load_page("admin.py")
elif choice == "User Terminal":
    load_page("user.py")
