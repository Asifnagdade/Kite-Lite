import streamlit as st
import pandas as pd
import os

st.title("🔑 Master Control Panel")

# --- DATABASE LOGIC ---
def load_users():
    if os.path.exists("users.csv"):
        return pd.read_csv("users.csv", dtype=str)
    return pd.DataFrame(columns=["username", "password", "role"])

def save_user(username, password, role):
    df = load_users()
    new_user = pd.DataFrame([[username, password, role]], columns=["username", "password", "role"])
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv("users.csv", index=False)
    return df

# --- USER CREATION FORM ---
st.subheader("Add New Admin/Partner")
with st.form("add_user_form"):
    new_name = st.text_input("Name (e.g. Aaliya)")
    new_pass = st.text_input("Set Password", value="1234")
    submit = st.form_submit_button("Create Admin ID")

    if submit:
        if new_name:
            # Username ko uniform banate hain: admin_aaliya
            full_username = f"admin_{new_name.lower().strip()}"
            save_user(full_username, new_pass, "admin")
            st.success(f"✅ Created! ID: {full_username} | Pass: {new_pass}")
            st.info("Ab aap Admin Portal par is ID se login kar sakte hain.")
        else:
            st.error("Please enter a name!")

# --- VIEW ALL USERS ---
st.divider()
st.subheader("All Active Users")
current_df = load_users()
st.table(current_df)

# Ek backup button taaki data kabhi khoye nahi
st.download_button(
    label="📥 Download Users Backup",
    data=current_df.to_csv(index=False),
    file_name="users_backup.csv",
    mime="text/csv"
)
