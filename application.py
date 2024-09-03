import streamlit as st
import requests

# Function to read ngrok URL from file
def get_ngrok_url():
    try:
        with open('/content/drive/MyDrive/ngrok_url.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        st.error("ngrok URL file not found. Make sure Colab is running and ngrok is started.")
        return None

# Get the ngrok URL
COLAB_API_URL = get_ngrok_url()

if COLAB_API_URL:
    # File upload option
    uploaded_file = st.file_uploader("Upload an audio or video file", type=["mp4", "wav", "mp3"])

    # Submit button
    if st.button("Submit"):
        if uploaded_file is not None:
            # Send the file to Colab for processing
            response = requests.post(COLAB_API_URL + "/process", files={"file": uploaded_file})

            if response.status_code == 200:
                file_path = response.json().get("file_path")
                st.success("File processed successfully! Click below to download the .docx file.")
                st.markdown(f"[Download .docx file]({file_path})")
            else:
                st.error("Failed to process the file. Please try again.")
        else:
            st.error("Please upload a file.")
else:
    st.error("Failed to retrieve the ngrok URL.")
