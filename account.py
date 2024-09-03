
import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
from streamlit_google_auth import Authenticate
import json
import tempfile

st.write("hello")

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

google_cred={"web":{
    "client_id":st.secrets["google_oauth"]["client_id"],
    "project_id":st.secrets["google_oauth"]["project_id"],
    "auth_uri":st.secrets["google_oauth"]["auth_uri"],
    "token_uri":st.secrets["google_oauth"]["token_uri"],
    "auth_provider_x509_cert_url":st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
    "client_secret":st.secrets["google_oauth"]["client_secret"],
    "redirect_uris":st.secrets["google_oauth"]["redirect_uris"]
}}
with tempfile.NamedTemporaryFile(delete=False, suffix=".json",mode='w') as temp_file:
    # Write JSON content to the temporary file
    json.dump(google_cred, temp_file)
    temp_file.flush()
    # Streamlit Authentication
authenticator = Authenticate(
    secret_credentials_path = temp_file.name,
    cookie_name='nixon_cookie_name',
    cookie_key='nixon_secret',
    redirect_uri="https://transcribers.streamlit.app/",
    )

def app():
    # Check if the user is authenticated
    authenticator.check_authentification()
    
    st.title('Account')    
    
    authenticator.login()
    
    if st.session_state['connected']:
        st.image(st.session_state['user_info'].get('picture'))
        st.write('Hello, '+ st.session_state['user_info'].get('name'))
        st.write('Your email is '+ st.session_state['user_info'].get('email'))
        if st.button('Log out'):
            authenticator.logout()
        
app()
