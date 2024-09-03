
import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
from streamlit_google_auth import Authenticate
import json
import tempfile

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
    
client_id=st.secrets["google_oauth"]["client_id"]
project_id=st.secrets["google_oauth"]["project_id"]
auth_uri=st.secrets["google_oauth"]["auth_uri"]
token_uri=st.secrets["google_oauth"]["token_uri"]
auth_provider_x509_cert_url=st.secrets["google_oauth"]["auth_provider_x509_cert_url"]
client_secret=st.secrets["google_oauth"]["client_secret"]
redirect_uris=st.secrets["google_oauth"]["redirect_uris"]


import os
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2


async def get_authorization_url(client: GoogleOAuth2, redirect_uri: str):
    """Get the URL for Google OAuth2 authorization."""
    authorization_url = await client.get_authorization_url(redirect_uri, scope=["profile", "email"])
    return authorization_url

async def get_access_token(client: GoogleOAuth2, redirect_uri: str, code: str):
    """Get the access token using the authorization code."""
    token = await client.get_access_token(code, redirect_uri)
    return token

async def get_email(client: GoogleOAuth2, token: str):
    """Get the user ID and email using the access token."""
    user_id, user_email = await client.get_id_email(token)
    return user_id, user_email

def get_login_str():
    """Generate a Google login URL."""
    client = GoogleOAuth2(client_id, client_secret)
    authorization_url = asyncio.run(get_authorization_url(client, redirect_uris))
    return f'<a target="_self" href="{authorization_url}">Google login</a>'

def display_user() -> None:
    """Display user information after login and provide logout option."""
    client = GoogleOAuth2(client_id, client_secret)
    # Retrieve the authorization code from the URL query parameters
    query_params = st.get_query_params()
    if 'code' in query_params:
        code = query_params['code'][0]
        # Get access token and user info
        token = asyncio.run(get_access_token(client, redirect_uris, code))
        user_id, user_email = asyncio.run(get_email(client, token['access_token']))
        st.write(f"You're logged in as {user_email} and your ID is {user_id}")

        # Logout button
        if st.button('Logout'):
            # Clear session state and re-run the app
            st.session_state.clear()
            st.rerun()
    else:
        st.error("Authorization code not found. Please ensure you have logged in.")

def app():
    """Main function to run the Streamlit app."""
    st.title("Google OAuth2 Authentication")

    # Display login or user info based on session state
    if 'code' in st.query_params:
        # Display user info if already authenticated
        display_user()
    else:
        # Show login link
        st.markdown(get_login_str(), unsafe_allow_html=True)
app()
