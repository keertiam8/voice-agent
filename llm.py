import os
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from tts import answer_to_speech

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    print("Error: GROQ_API_KEY environment variable not set.")
    raise SystemExit(1)

client = Groq(api_key=API_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"
CONVERSATION_HISTORY_FILE = "transcription/conversation_history.json"


def get_all_transcriptions(json_file="transcription/transcription_history.json"):
    """Get all transcriptions from history"""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        print(f"Error: {json_file} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: {json_file} is not valid JSON")
        return []


def load_context(txt_file="data/data.txt"):
    """Load context/prompt from data/data.txt"""
    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {txt_file} not found")
        return ""


def load_conversation_history():
    """Load previous conversation history for context"""
    if os.path.exists(CONVERSATION_HISTORY_FILE):
        try:
            with open(CONVERSATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:  # File is empty
                    return []
                return json.loads(content)
        except:
            return []
    return []


def build_context_from_history(conv_history):
    """Build context string from previous conversation"""
    if not conv_history:
        return ""
    context_str = "Previous conversation history:\n\n"
    for entry in conv_history:
        context_str += f"Q: {entry.get('question', '')}\n"
        context_str += f"A: {entry.get('answer', '')}\n\n"
    return context_str


def send_to_groq(question, base_context, conversation_history):
    """Send question to Groq with context and conversation history"""

    if not question:
        print("No question provided")
        return ""

    # Build system message with base context + conversation history
    prev_conv = build_context_from_history(conversation_history)
    system_msg = f"""You are a fintech assistant for Razorpay.
Answer ONLY using the context below.
If the answer is not present, say: "I don't know."

Context:
{base_context}

{prev_conv}"""

    print(f"Sending to Groq: {question}")
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0.3,
        max_tokens=128,
    )

    return response.choices[0].message.content.strip()


def save_conversation_entry(question, answer):
    """Save Q&A pair to conversation history"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(CONVERSATION_HISTORY_FILE), exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer
    }
    
    conv_history = load_conversation_history()
    conv_history.append(entry)
    
    with open(CONVERSATION_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(conv_history, f, ensure_ascii=False, indent=2)


def get_answer(transcription_history_json="transcription/transcription_history.json",
               context_file="data/data.txt"):
    """Process all transcriptions in history with context and conversation memory"""
    all_transcriptions = get_all_transcriptions(transcription_history_json)
    base_context = load_context(context_file)
    conv_history = load_conversation_history()

    if not all_transcriptions:
        print("No transcriptions available")
        return []

    if not base_context:
        print("Warning: No context loaded; using transcriptions alone")

    # Get the latest transcription that hasn't been answered yet
    # (compare with conversation history to avoid duplicate answers)
    answered_questions = {entry.get("question") for entry in conv_history}
    
    results = []
    for trans_entry in all_transcriptions:
        question = trans_entry.get("text", "")
        
        if not question:
            continue
        
        # Skip if already answered
        if question in answered_questions:
            print(f"Skipping already-answered question: {question}")
            continue
        
        answer = send_to_groq(question, base_context, conv_history)
        save_conversation_entry(question, answer)
        
        # Convert answer to speech
        audio_file = answer_to_speech(answer, auto_play=True)
        
        # Add to local conversation history for next iteration
        conv_history.append({
            "question": question,
            "answer": answer
        })
        
        results.append({
            "question": question,
            "answer": answer,
            "audio_file": audio_file
        })
        
        print(f"\nAnswer: {answer}\n")
    
    return results


if __name__ == "__main__":
    response = get_answer()