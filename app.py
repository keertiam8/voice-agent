import streamlit as st
import os
import json
from datetime import datetime
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import time

# Import local modules
from stt import Recorder, transcribe_audio
from llm import get_answer
from tts import answer_to_speech

st.set_page_config(page_title="Voice Agent", layout="wide")
st.title("🎤 Voice Agent - Ask Razorpay Questions")

# Initialize session state
if "recording" not in st.session_state:
    st.session_state.recording = False
if "recorder" not in st.session_state:
    st.session_state.recorder = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "answer" not in st.session_state:
    st.session_state.answer = None
if "response_audio" not in st.session_state:
    st.session_state.response_audio = None
if "last_recording_time" not in st.session_state:
    st.session_state.last_recording_time = 0

# Create columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Record Your Question")
    
    # Record button
    record_clicked = st.button("🎙️ Start Recording" if not st.session_state.recording else "⏹️ Stop Recording", 
                               key="record_btn", use_container_width=True)
    
    if record_clicked:
        if not st.session_state.recording:
            # Start recording - reset previous transcript/answer
            st.session_state.transcript = None
            st.session_state.answer = None
            st.session_state.response_audio = None
            st.session_state.audio_file = "temp_recording.wav"
            st.session_state.recording = True
            st.session_state.recorder = Recorder(filename=st.session_state.audio_file)
            st.session_state.recorder.start()
            st.write("🔴 Recording... Click Stop to finish")
            st.rerun()
        else:
            # Stop recording
            st.session_state.recorder.stop()
            st.session_state.recording = False
            st.session_state.last_recording_time = datetime.now().timestamp()
            st.write("✅ Recording saved!")
            st.rerun()
    
    # Show recording status
    if st.session_state.recording:
        st.warning("🔴 Recording in progress...")
    
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file) and not st.session_state.recording:
        st.success(f"✅ Recording saved: {st.session_state.audio_file}")
        with open(st.session_state.audio_file, "rb") as audio:
            st.audio(audio.read(), format="audio/wav")

with col2:
    st.subheader("2. Answer from AI")
    
    # Automatically process when audio file is saved and not yet processed
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file) and st.session_state.transcript is None:
        with st.spinner("Transcribing..."):
            # Step 1: STT
            transcript = transcribe_audio(st.session_state.audio_file)
            st.session_state.transcript = transcript
        
        if transcript:
            with st.spinner("Getting answer from AI..."):
                # Step 2: LLM
                results = get_answer()
                if results:
                    answer_text = results[-1].get("answer", "")
                    st.session_state.answer = answer_text
            
            if st.session_state.answer:
                with st.spinner("Converting to speech and playing..."):
                    # Step 3: TTS
                    audio_file = answer_to_speech(st.session_state.answer, auto_play=False)
                    st.session_state.response_audio = audio_file
                
                if st.session_state.response_audio and os.path.exists(st.session_state.response_audio):
                    # Display audio player with autoplay (no text, just audio)
                    with open(st.session_state.response_audio, "rb") as audio:
                        st.audio(audio.read(), format="audio/wav", autoplay=True)
        else:
            st.error("Failed to transcribe audio")
    elif st.session_state.response_audio and os.path.exists(st.session_state.response_audio):
        # Show audio for previously processed questions
        with open(st.session_state.response_audio, "rb") as audio:
            st.audio(audio.read(), format="audio/wav", autoplay=True)
    else:
        st.info("👆 Record a question first")

# Sidebar - Show history
st.sidebar.title("📋 Conversation History")

try:
    if os.path.exists("transcription/conversation_history.json"):
        with open("transcription/conversation_history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
        
        if history:
            st.sidebar.write(f"**Total Q&A: {len(history)}**")
            for i, entry in enumerate(reversed(history[-5:]), 1):  # Show last 5
                with st.sidebar.expander(f"Q{len(history)-i+1}: {entry.get('question', '')[:50]}..."):
                    st.write(f"**Q:** {entry.get('question', '')}")
                    st.write(f"**A:** {entry.get('answer', '')}")
                    st.write(f"**Time:** {entry.get('timestamp', '')}")
        else:
            st.sidebar.info("No conversation history yet")
    else:
        st.sidebar.info("No conversation history file")
except json.JSONDecodeError:
    st.sidebar.error("⚠️ Conversation history file is corrupted. Starting fresh.")
except Exception as e:
    st.sidebar.error(f"Error reading history: {str(e)}")

# Footer
st.divider()
st.caption("🎯 Flow: Record → Transcribe (STT) → AI Answer (Groq) → Text-to-Speech (TTS) → Voice Output")
