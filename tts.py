import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY_TTS")
if not API_KEY:
    print("Error: DEEPGRAM_API_KEY_TTS environment variable not set.")
    raise SystemExit(1)


def text_to_speech(text, output_file=None, voice="aura-asteria-en"):
    """Convert text to speech using Deepgram TTS API
    
    Args:
        text: The text to convert to speech
        output_file: Optional output file path (default: timestamped audio.wav in audios/)
        voice: Deepgram voice model (default: aura-asteria-en)
    
    Returns:
        Path to saved audio file
    """
    if not text:
        print("No text provided for TTS")
        return None
    
    # Create audios folder if it doesn't exist
    audios_dir = "audios"
    if not os.path.exists(audios_dir):
        os.makedirs(audios_dir)
    
    # Generate output filename with timestamp if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(audios_dir, f"response_{timestamp}.wav")
    
    # Deepgram TTS endpoint
    url = f"https://api.deepgram.com/v1/speak?model={voice}&encoding=linear16"
    
    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text
    }
    
    print(f"Converting to speech: {text[:100]}...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Save audio to file
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        print(f"Audio saved to: {output_file}")
        return output_file
    
    except requests.exceptions.RequestException as e:
        print(f"Error converting text to speech: {e}")
        return None


def play_audio(audio_file):
    """Play audio file using platform-specific command"""
    import subprocess
    import platform
    
    if not os.path.exists(audio_file):
        print(f"Audio file not found: {audio_file}")
        return
    
    try:
        if platform.system() == "Windows":
            # Use winsound for direct audio playback on Windows
            import winsound
            winsound.PlaySound(audio_file, winsound.SND_FILENAME)
            print(f"Playing: {audio_file}")
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["afplay", audio_file])
            print(f"Playing: {audio_file}")
        else:  # Linux
            subprocess.run(["ffplay", "-nodisp", "-autoexit", audio_file])
            print(f"Playing: {audio_file}")
    except Exception as e:
        print(f"Error playing audio: {e}")


def answer_to_speech(answer_text, auto_play=True):
    """Convert answer text to speech and optionally play it
    
    Args:
        answer_text: The answer from LLM
        auto_play: Whether to play audio immediately (default: True)
    
    Returns:
        Path to saved audio file
    """
    audio_file = text_to_speech(answer_text)
    
    if audio_file and auto_play:
        play_audio(audio_file)
    
    return audio_file


if __name__ == "__main__":
    sample_text = "Hello! This is a test of the text-to-speech functionality."
    answer_to_speech(sample_text)
    
