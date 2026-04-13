import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    print("Error: DEEPGRAM_API_KEY environment variable not set.")
    raise SystemExit(1)


def transcribe_file(wav_file):
    if not os.path.exists(wav_file):
        print(f"Error: {wav_file} not found")
        return ""
    
    with open(wav_file, "rb") as audio_file:
        audio_bytes = audio_file.read()
    
    url = "https://api.deepgram.com/v1/listen?language=en-US"
    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "audio/wav"
    }
    
    try:
        response = requests.post(url, headers=headers, data=audio_bytes)
        response.raise_for_status()
        result = response.json()
        
        transcript = ""
        try:
            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        except Exception:
            transcript = result.get("results", "")
        
        if not os.path.exists("transcription"):
            os.makedirs("transcription")
        
        out = {
            "text": transcript,
            "language": "en",
            "timestamp": datetime.now().isoformat(),
            "raw": result
        }
        
        with open("transcription/transcription.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        
        history_file = "transcription/transcription_history.json"
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(out)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        return transcript
    
    except requests.exceptions.RequestException as e:
        print(f"Error transcribing: {e}")
        return ""
