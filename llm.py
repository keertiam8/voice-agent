import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    print("Error: GROQ_API_KEY environment variable not set.")
    raise SystemExit(1)

client = Groq(api_key=API_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"


def load_transcription_text(json_file="transcription.json"):
    """Extract text from transcription.json"""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("text", "")
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        return ""
    except json.JSONDecodeError:
        print(f"Error: {json_file} is not valid JSON")
        return ""


def load_prompt(txt_file="data.txt"):
    """Load initial prompt from data.txt"""
    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {txt_file} not found")
        return ""


def send_to_groq(transcription_text, initial_prompt):
    """Send transcription with controlled prompt to Groq"""

    if not transcription_text:
        print("No transcription text provided")
        return ""

    print("Sending to Groq...")
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": f"""You are a fintech assistant for Razorpay.
Answer ONLY using the context below.
If the answer is not present, say: "I don't know."

Context:
{initial_prompt}"""
            },
            {
                "role": "user",
                "content": transcription_text
            }
        ],
        temperature=0.3,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()


def process_audio_with_groq(transcription_json="transcription.json",
                             prompt_file="data/data.txt"):
    """Load files and process with Groq"""
    transcription = load_transcription_text(transcription_json)
    initial_prompt = load_prompt(prompt_file)

    if not transcription:
        print("No transcription available")
        return ""

    if not initial_prompt:
        print("Warning: No initial prompt loaded; using transcription alone")

    result = send_to_groq(transcription, initial_prompt)
    print("\nGroq Response:")
    print(result)
    return result


if __name__ == "__main__":
    response = process_audio_with_groq()