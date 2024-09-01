import streamlit as st
import whisperx
import ffmpeg
import os
import subprocess
from datetime import datetime
import time
from docx import Document

# Define folder paths
temp_folder = "temp_files"
output_folder = "output_files"
log_file = os.path.join(output_folder, "processing_log.txt")

# Ensure temp and output directories exist
os.makedirs(temp_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

def log_activity(message):
    """Logs activity with a timestamp to the global log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {message}\n")

def format_duration(seconds):
    """Converts seconds to a human-readable format like '1 min 29 sec'."""
    minutes, seconds = divmod(seconds, 60)
    if minutes > 0:
        return f"{int(minutes)} min {int(seconds)} sec"
    else:
        return f"{int(seconds)} sec"

def format_timestamp(seconds):
    """Converts seconds to HH:MM:SS format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def extract_audio(video_path):
    """Extracts audio from a video file and saves it as a .wav file in the temp folder."""
    filename = os.path.splitext(os.path.basename(video_path))[0]
    output_file = os.path.join(temp_folder, f"{filename}_$.wav")

    log_activity(f"Calling extract_audio for {video_path}.")

    try:
        ffmpeg.input(video_path).output(output_file).run(quiet=True, overwrite_output=True)
        log_activity(f"Audio extracted to {output_file}.")
        return output_file
    except Exception as e:
        log_activity(f"Error extracting audio: {e}")
        return None

def apply_noise_reduction(input_file, noise_profile_strength=0.15):
    """Applies noise reduction using SoX and returns the path to the cleaned audio file."""
    filename = os.path.splitext(os.path.basename(input_file))[0]
    noise_profile = os.path.join(temp_folder, f"{filename}.prof")
    output_file = os.path.join(temp_folder, f"{filename}_cleaned.wav")

    log_activity(f"Calling apply_noise_reduction for {input_file}.")

    try:
        subprocess.run(['sox', input_file, '-n', 'noiseprof', noise_profile], check=True)
        log_activity(f"Noise profile generated at {noise_profile}.")

        subprocess.run(['sox', input_file, output_file, 'noisered', noise_profile, str(noise_profile_strength)], check=True)
        log_activity(f"Noise reduction applied. Cleaned file saved at {output_file}.")
        return output_file
    except subprocess.CalledProcessError as e:
        log_activity(f"Error during noise reduction: {e}")
        return None

def get_audio_duration(audio_file):
    """Returns the duration of the audio file in seconds."""
    try:
        probe = ffmpeg.probe(audio_file)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        log_activity(f"Error getting audio duration: {e}")
        return 0

def process_audio(video_path):
    """Processes the video to extract and clean audio, returning the cleaned audio path."""
    log_activity("***************" * 5)
    log_activity(f"Processing audio for {video_path}.")
    log_activity("***************" * 5)

    # Log file size
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # Size in MB
    log_activity(f"File size: {file_size:.2f} MB.")

    start_time = time.time()

    wav_file = extract_audio(video_path)
    if wav_file:
        cleaned_audio = apply_noise_reduction(wav_file)

        # Log the duration of the cleaned audio
        duration = get_audio_duration(cleaned_audio)
        formatted_duration = format_duration(duration)
        log_activity(f"Audio duration: {formatted_duration}.")

        log_activity(f"Temporary files: {wav_file}, {cleaned_audio}")

        end_time = time.time()
        time_taken = format_duration(end_time - start_time)
        log_activity(f"Time taken to process audio: {time_taken}.")

        return cleaned_audio

    log_activity("Processing audio failed.")
    return None

def transcribe_audio_with_whisperx(audio_file):
    """Transcribes the given audio file using WhisperX and saves the transcription to a .docx file."""
    log_activity(f"Starting transcription for {audio_file}.")

    device = "cpu"  # Use 'cuda' if a GPU is available
    batch_size = 4
    compute_type = "int8"

    try:
        model = whisperx.load_model("medium", device, compute_type=compute_type,language='en')
        log_activity("Whisper model loaded.")

        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size)
        log_activity("Transcription completed.")

        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
        log_activity("Alignment completed.")

        diarize_model = whisperx.DiarizationPipeline(use_auth_token="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", device=device)
        diarize_segments = diarize_model(audio)
        final_result = whisperx.assign_word_speakers(diarize_segments, aligned_result)
        log_activity("Speaker diarization completed.")

        filename = os.path.splitext(os.path.basename(audio_file))[0]
        output_file = os.path.join(output_folder, f"{filename}.docx")
        document = Document()

        current_speaker = None
        current_segment_start = None
        current_segment_end = None
        segment_text = []

        for segment in final_result["segments"]:
            start = segment["start"]
            end = segment["end"]
            speaker = segment.get("speaker", "Unknown Speaker")
            text = segment["text"]

            if speaker != current_speaker:
                if current_speaker is not None:
                    document.add_paragraph(f"[{format_timestamp(current_segment_start)} - {format_timestamp(current_segment_end)}] {current_speaker}: {' '.join(segment_text)}\n")
                current_speaker = speaker
                current_segment_start = start
                current_segment_end = end
                segment_text = [text]
            else:
                current_segment_end = end
                segment_text.append(text)

        if current_speaker is not None:
            document.add_paragraph(f"[{format_timestamp(current_segment_start)} - {format_timestamp(current_segment_end)}] {current_speaker}: {' '.join(segment_text)}\n")

        document.save(output_file)
        log_activity(f"Transcription saved to {output_file}.")
        return output_file

    except Exception as e:
        log_activity(f"Error during transcription: {e}")
        return None

def app():
    st.title("Transcription Service")
    st.write("Upload an audio or video file, and get a transcribed .docx file with speaker diarization.")

    uploaded_file = st.file_uploader("Choose an audio or video file", type=["wav", "mp4", "mkv", "avi","mp3"])

    if uploaded_file is not None:
        # Save the uploaded file temporarily
        file_path = os.path.join(temp_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File {uploaded_file.name} uploaded successfully!")

        # Add a button to start the transcription process
        if st.button("Transcribe"):
            st.write("Processing the file...")
            processed_audio = process_audio(file_path)

            if processed_audio:
                st.write("Transcribing the audio...")
                docx_file = transcribe_audio_with_whisperx(processed_audio)

                if docx_file:
                    st.write("Transcription complete!")
                    with open(docx_file, "rb") as f:
                        st.download_button(
                            label="Download Transcription",
                            data=f,
                            file_name=os.path.basename(docx_file),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                    st.markdown(f"**[Download your transcription]({docx_file})**")
                else:
                    st.error("Failed to transcribe the audio.")
            else:
                st.error("Failed to process the file.")