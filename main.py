import streamlit as st
from streamlit_option_menu import option_menu
import account, application
import os



def run():
    st.header("Welcome to Transcribers")
    with st.sidebar:
        app=option_menu(
        menu_title='Transcribers',
        options=['Account','Transcribe'],
        icons=['person-circle','trophy-fill'],
        menu_icon='chat-text-fill',
        default_index=1
        )

    if app =='Account': 
        account.app()
    if app=='Transcribe': 
        application.app()
run()
