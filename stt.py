import os
import json
import requests
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# Recording settings
fs = 44100
device = None
seconds = 10

api_key = os.getenv("DEEPGRAM_API_KEY")
if not api_key:
	print("Error: DEEPGRAM_API_KEY environment variable not set.")
	print("Set it and re-run, e.g. on Windows:")
	print(r"set DEEPGRAM_API_KEY=your_key_here")
	raise SystemExit(1)

print("Speak now...")
recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16', device=device)
sd.wait()
write("input.wav", fs, recording)
print("Processing with Deepgram...")

with open("input.wav", "rb") as audio_file:
	audio_bytes = audio_file.read()

# Send to Deepgram
url = "https://api.deepgram.com/v1/listen?language=en-US"
headers = {
	"Authorization": f"Token {api_key}",
	"Content-Type": "audio/wav"
}
resp = requests.post(url, headers=headers, data=audio_bytes)
resp.raise_for_status()
result = resp.json()
transcript = ""
try:
	transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
except Exception:
	transcript = result.get("results", "")

print("You said:", transcript)

out = {
	"text": transcript,
	"language": "en",
	"timestamp": datetime.now().isoformat(),
	"raw": result
}

# Save current transcription (for llm.py to use)
with open("transcription/transcription.json", "w", encoding="utf-8") as f:
	json.dump(out, f, ensure_ascii=False, indent=2)

# Append to history (keep all transcriptions)
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

print(f"Saved to transcription/ folder (total: {len(history)} transcriptions)")