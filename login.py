import streamlit as st

# --- USER CREDENTIALS (Temporary Storage) ---
if "user_credentials" not in st.session_state:
    st.session_state["user_credentials"] = {
        "admin": {"password": "admin123", "role": "Admin"},
        "doc_checker": {"password": "doc456", "role": "Document Checker"},
        "loan_agent": {"password": "loan789", "role": "Loan Agent"},
    }

# --- LOGIN FUNCTION ---
def login_user(username, password):
    """Validate user login."""
    users = st.session_state["user_credentials"]
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

# --- SIGN-UP FUNCTION ---
def signup_user(username, password, role):
    """Register a new user."""
    if username in st.session_state["user_credentials"]:
        return False  # User already exists
    st.session_state["user_credentials"][username] = {"password": password, "role": role}
    return True

# --- SHOW LOGIN FORM ---
def show_login():
    """Display login or sign-up options."""
    st.title("🔐 Login to Helpdesk")

    # Toggle between login and sign-up
    option = st.radio("Choose an option:", ["Login", "Sign Up"])

    if option == "Login":
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("Login"):
            role = login_user(username, password)
            if role:
                st.success(f"✅ Login successful! Role: {role}")
                st.session_state["role"] = role
                st.session_state["logged_in"] = True
                st.success(f"Welcome {username} ")
            else:
                st.error("❌ Invalid username or password.")

    elif option == "Sign Up":
        st.subheader("📝 Create a New Account")
        new_username = st.text_input("👤 Choose a username")
        new_password = st.text_input("🔒 Set a password", type="password")
        role = st.selectbox("🎭 Select your role", ["Document Checker", "Loan Agent", "Admin"])

        if st.button("Sign Up"):
            if signup_user(new_username, new_password, role):
                st.success("🎉 Account created successfully! Please login.")
            else:
                st.error("⚠️ Username already exists. Please choose a different username.")

