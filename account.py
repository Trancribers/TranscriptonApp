
import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
from streamlit_google_auth import Authenticate, CookieHandler

# Firebase Setup
firebase_cred = {
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"],
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"],
    "auth_uri": st.secrets["firebase"]["auth_uri"],
    "token_uri": st.secrets["firebase"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
}

cred = credentials.Certificate(firebase_cred)
try:
    firebase_admin.get_app()
except ValueError as e:
    initialize_app(cred)


# Streamlit Authentication
credentials = Authenticate(
    secret_credentials_path = google_oauth_cred.json,
    cookie_name='my_cookie_name',
    cookie_key='this_is_secret',
    redirect_uri="https://transcribers.streamlit.app/",
)

def app():
    st.title("Account")

    if credentials:
        st.write(f"Logged in as: {credentials['name']}")
        st.write(f"Your email: {credentials['email']}")
        if st.button("Logout", type="primary", key="logout"):
            st.session_state.email = None
            st.experimental_rerun()  # Refresh the page
    else:
        st.markdown(f'<a href="{credentials.authorization_url}" target="_self">Login with Google</a>', unsafe_allow_html=True)

app()
