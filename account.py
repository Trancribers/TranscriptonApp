import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2

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

cred=credentials.Certificate(firebase_cred)
try:
    firebase_admin.get_app()
except ValueError as e:
    initialize_app(cred)

#initialize google oauth2 client
client_id= st.secrets["google_oauth"]["client_id"]
client_secrets= st.secrets["google_oauth"]["client_secret"]
redirect_url = "https://transcribers.streamlit.app/"

client=GoogleOAuth2(client_id=client_id,client_secret=client_secrets)

if 'email' not in st.session_state:
    st.session_state.email = None

async def get_access_token(client:GoogleOAuth2,redirect_url: str,code: str):
    return await client.get_access_token(code,redirect_url)

async def get_email(client:GoogleOAuth2,token:str):
    user_id,user_email = await client.get_id_email(token)
    return user_id, user_email

def get_logged_in_user_email():
    try:
        query_params = st.query_params
        code = query_params.get('code')
        if code:
            token=asyncio.run(get_access_token(client,redirect_url,code[0]))
            st.query_params

            if token:
                user_id,user_email=asyncio.run(get_email(client,token['access_token']))
                if user_email:
                    try:
                        user=auth.get_user_by_email(user_email)
                    except exceptions.FirebaseError:
                        user=auth.create_user(email=user_email)

                    st.session_state.email=user_email
                    return user.email
    except Exception as e:
        st.error(f"an error accurred:{e}")

def show_login_button():
    try:
        authorization_url = asyncio.run(client.get_authorization_url(
            redirect_url,
            scope=["email", "profile"],
            extras_params={"access_type": "offline"}
        ))
        st.write(f"Authorization URL: {authorization_url}")  # Debug: Print the URL
        st.markdown(f'<a href="{authorization_url}" target="_self">Login</a>', unsafe_allow_html=True)
        get_logged_in_user_email()
    except Exception as e:
        st.error(f"An error occurred while generating the login URL: {e}")

def refresh_page():
    """Force refresh of the page using JavaScript."""
    st.markdown("""
        <script>
        window.location.reload();
        </script>
    """, unsafe_allow_html=True)
    
def app():
    st.title("Account")

    if 'email' not in st.session_state:
        st.session_state.email = None

    if not st.session_state.email:
        get_logged_in_user_email()
        show_login_button()

    if st.session_state.email:
        st.write(st.session_state.email)
        if st.button("Logout",type="primary", key="logout_non_requiured"):
            st.session_state.email=None
            refresh_page()
app()
