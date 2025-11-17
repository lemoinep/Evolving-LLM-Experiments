# Author(s): Dr. Patrick Lemoine

import os
import json
import subprocess
import psutil
import requests
from datetime import datetime
import pyttsx3
import ollama


OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAMES = ["qwen2.5-coder:7b", "gpt-oss:20b", "deepseek-r1:8b"]  

SUMMARY_MODEL = "qwen2.5-coder:7b"

JSON_PATH = "ollama_path.json"

def save_path_to_json(path):
    with open(JSON_PATH, "w") as f:
        json.dump({"ollama_path": path}, f)

def load_path_from_json():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            data = json.load(f)
            return data.get("ollama_path")
    return None

def launch_speech_if_needed():
    global engine
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', int(rate))
    volume = engine.getProperty('volume')
    engine.setProperty('volume', float(volume))
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)

def play_speech(text):
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def find_ollama_executable():
    for path_dir in os.getenv('PATH').split(os.pathsep):
        candidate = os.path.join(path_dir, "Ollama.exe")
        if os.path.isfile(candidate):
            return candidate
    potential_dirs = [r"C:\Program Files\Ollama", r"C:\Program Files (x86)\Ollama"]
    for d in potential_dirs:
        candidate = os.path.join(d, "Ollama.exe")
        if os.path.isfile(candidate):
            return candidate
    return None

def is_ollama_running():
    for proc in psutil.process_iter(['name']):
        try:
            if "Ollama" in proc.info['name']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def launch_ollama_if_needed():
    path = load_path_from_json()
    if path is None or not os.path.isfile(path):
        path = find_ollama_executable()
        if path:
            save_path_to_json(path)
        else:
            print("Ollama.exe not found on the system.")
            return False
    if not is_ollama_running():
        subprocess.Popen([path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Launching Ollama from: {path}")
    else:
        print("Ollama is already running.")
    return True

def list_models():
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        else:
            print(f"Failed to fetch models: {response.status_code} {response.text}")
            return []
    except Exception as e:
        print(f"Error connecting to Ollama server: {e}")
        return []

def ask_ollama(model, prompt, stream=False):
    url = f"{OLLAMA_BASE_URL}/api/generate"
    data = {
        "model": model,
        "prompt": prompt,
        "stream": stream
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response field in reply.")
        else:
            print(f"Generation error: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Ollama request error: {e}")
        return None

def synthesize_responses(responses):
    combined = "\n\n".join(responses)
    synthesis_prompt = f"Please provide a concise synthesis of the following answers:\n{combined}"
    return ask_ollama(SUMMARY_MODEL, synthesis_prompt)

def main(chat_path, use_speech):
    if use_speech:
        launch_speech_if_needed()

    if not launch_ollama_if_needed():
        print("Failed to start Ollama.")
        return

    models_available = list_models()
    missing = [m for m in MODEL_NAMES if m not in models_available]
    if missing:
        print(f"Missing local models: {missing}")
        print(f"Available models: {models_available}")
        return

    os.makedirs(chat_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(chat_path, f"ollama_conversation_{timestamp}.txt")
    
    user_input = input("👦: ")

    print("Starting queries to local models...")
    responses = []
    for model in MODEL_NAMES:
        print(f"Querying the model : {model}")
            
        response = ask_ollama(model, user_input)
        
        if response:
            print(f"{model} Response : {response}\n")
            responses.append(response)
        else:
            print(f"No response received from model {model}.\n")

    if not responses:
        print("No valid response received, ending.")
        return

    print("Synthesizing responses...")
    synthesis = synthesize_responses(responses)
    print("Final Synthesis :\n", synthesis)
    
    print("Verifying the responses...")
    synthesis = synthesize_responses("Can you verify this answer : "+synthesis+". Is it correct ?")
    print("Final Synthesis :\n", synthesis)

    if use_speech and synthesis:
        play_speech(synthesis)

    # Saving to file
    with open(filename, "w", encoding="utf-8") as f:
        for i, model_response in enumerate(responses):
            f.write(f"Response from {MODEL_NAMES[i]}:\n{model_response}\n\n")
        f.write("Final Synthesis:\n")
        f.write(synthesis or "")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query local Ollama with local models.")
    parser.add_argument("--Path", type=str, default=".", help="Folder to save the conversation")
    parser.add_argument("--Speech", type=int, default=0, help="Activate speech synthesis (1 or 0)")
    parser.add_argument("--URL", type=str, default="http://localhost:11434", help="Base Ollama URL")
    parser.add_argument("--Models", type=str, default="qwen2.5-coder:7b,gpt-oss:20b,deepseek-r1:8b",
                        help="List of local models, separated by commas")
    parser.add_argument("--SummaryModel", type=str, default="qwen2.5-coder:7b", help="Synthesis model")

    args = parser.parse_args()

    OLLAMA_BASE_URL = args.URL
    MODEL_NAMES = [m.strip() for m in args.Models.split(",")]
    SUMMARY_MODEL = args.SummaryModel

    main(args.Path, args.Speech == 1)

