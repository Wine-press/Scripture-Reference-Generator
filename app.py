import streamlit as st
from google import genai
import os

# Web App UI Configuration
st.title("Sermon Scripture to Lower-Third SRT Generator")
st.write("Upload a complete MP3/WAV sermon audio file to automatically generate scripture lower-third subtitles.")

# Securely request API key from your team member (or hardcode it if private)
api_key = st.text_input("Enter the Gemini API Key:", type="password")
uploaded_file = st.file_uploader("Upload Audio Sermon (MP3/WAV)", type=["mp3", "wav", "m4a"])

if st.button("Generate SRT") and uploaded_file and api_key:
    # Save file locally temporarily for processing
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.info("Uploading audio to Gemini... This will take a moment based on file size.")
    
    try:
        # Initialize Gemini SDK
        client = genai.Client(api_key=api_key)
        
        # Upload the audio file directly to Gemini's server
        gemini_file = client.files.upload(file=temp_path)
        st.info("Audio uploaded successfully! Extracting timestamps and scriptures...")
        
        # The Master Prompt for direct audio processing
        prompt = """
        You are an expert subtitle extraction tool for video post-production. You are analyzing an audio sermon.
        Listen to the entire audio file and extract all explicit and implicit scriptural references, formatting them into a standard, continuous SRT file.
        
        CRITICAL INSTRUCTION: Output ONLY the raw, pure SRT text data. Do not include markdown blocks like ``` or any conversational filler. The first character must be "1".
        
        1. TIMESTAMPS (DURATION): 
        - The IN point must be the exact moment the speaker begins referencing the scripture.
        - The OUT point must be the moment they finish discussing or reading the passage.
        - Format: 00:00:00,000 --> 00:00:00,000
        
        2. SCRIPTURE VERSIONING:
        - Default to (KJV).
        - If the speaker explicitly mentions a different translation, change the suffix to match (NIV, MSG, AMP, etc.).
        
        3. TEXT CONTENT (REFERENCE + VERSE):
        - Line 1: Scriptural Reference (e.g., 1 Corinthians 2:10 (KJV)).
        - Line 2+: The exact, accurate biblical text of that verse retrieved from your internal knowledge base. Do not rely solely on spoken words as they may paraphrase; output the accurate biblical text.
        
        4. SRT SYNTAX:
        - Sequence number goes first.
        - Timestamp arrow must be `-->` with commas for milliseconds.
        """
        
        # Call Gemini 1.5 Pro to process audio + prompt
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[gemini_file, prompt]
        )
        
        st.success("Extraction Complete!")
        
        # Clean up the output to ensure it's pure SRT
        srt_output = response.text.replace("```srt", "").replace("```", "").strip()
        
        # Display output and provide download button
        st.text_area("Generated SRT Preview", srt_output, height=400)
        st.download_button(
            label="Download .srt File",
            data=srt_output,
            file_name="sermon_scriptures.srt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
