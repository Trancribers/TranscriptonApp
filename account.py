import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2


cred=credentials.Certificate("transcribers-47789-5a88ac1ae51c.json")
try:
    firebase_admin.get_app()
except ValueError as e:
    initialize_app(cred)

#initialize google oauth2 client
client_id= st.secrets["client_id"]
client_secrets= st.secrets["client_secret"]
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
        query_params = st.experimental_get_query_params()
        code = query_params.get('code')
        if code:
            token=asyncio.run(get_access_token(client,redirect_url,code))
            st.query_params()

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
    authorization_url=asyncio.run(client.get_authorization_url(
        redirect_url,
        scope=["email","profile"],
        extras_params={"access_type":  "offline"}
    ))
    st.markdown(f'<a href="{authorization_url}" target="_self">Login</a>',unsafe_allow_html=True)
    get_logged_in_user_email()

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
            st.experimental_rerun()
app()
