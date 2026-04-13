import os
import json
import requests
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import threading

load_dotenv()

fs = 44100
device = None

api_key = os.getenv("DEEPGRAM_API_KEY")
if not api_key:
	print("Error: DEEPGRAM_API_KEY environment variable not set.")
	print("Set it and re-run, e.g. on Windows:")
	print(r"set DEEPGRAM_API_KEY=your_key_here")
	raise SystemExit(1)


class Recorder:
	def __init__(self, filename="recording.wav"):
		self.filename = filename
		self.stream = None
		self.recording = None
		self.is_recording = False
	
	def start(self):
		if self.is_recording:
			return
		
		self.is_recording = True
		self.recording = []
		
		def audio_callback(indata, frames, time, status):
			if status:
				print(f"Audio status: {status}")
			self.recording.append(indata.copy())
		
		self.stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', 
									  callback=audio_callback, blocksize=1024)
		self.stream.start()
	
	def stop(self):
		if not self.is_recording:
			return
		
		self.is_recording = False
		if self.stream:
			self.stream.stop()
			self.stream.close()
		
		if self.recording:
			audio_data = np.concatenate(self.recording, axis=0)
			write(self.filename, fs, audio_data)
			return self.filename
		return None


def transcribe_audio(wav_file):
	if not os.path.exists(wav_file):
		print(f"Error: {wav_file} not found")
		return ""
	
	with open(wav_file, "rb") as audio_file:
		audio_bytes = audio_file.read()
	
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
	
	if not os.path.exists("transcription"):
		os.makedirs("transcription")
	
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
	
	print(f"Saved to transcription/ folder (total: {len(history)} transcriptions)")
	return transcript


if __name__ == "__main__":
	print("Speak now...")
	recorder = Recorder("input.wav")
	recorder.start()
	import time
	time.sleep(10)
	recorder.stop()
	print("Processing with Deepgram...")
	transcribe_audio("input.wav")