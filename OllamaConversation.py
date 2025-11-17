# Author(s): Dr. Patrick Lemoine

import os
import sys
import json
import subprocess
import psutil
import requests
from datetime import datetime
import pyttsx3



OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:7b"

#MODEL_NAME = "gpt-oss:20b"
#MODEL_NAME = "deepseek-r1:8b"

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
    rate = 100
    volume = 1.0
    num_voice = 1

    engine = pyttsx3.init() 
    rate = engine.getProperty('rate')
    engine.setProperty('rate', int(rate))
    volume = engine.getProperty('volume')
    engine.setProperty('volume', int(volume))
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[num_voice].id)
   
def play_speech(text):
    engine.say(text)
    engine.runAndWait()
    engine.stop()
    
def find_ollama_executable():
    # Search in PATH
    for path_dir in os.getenv('PATH').split(os.pathsep):
        candidate = os.path.join(path_dir, "Ollama.exe")
        if os.path.isfile(candidate):
            return candidate
    # Search typical install folders on Windows
    potential_dirs = [
        r"C:\Program Files\Ollama",
        r"C:\Program Files (x86)\Ollama",
    ]
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
            return
    if not is_ollama_running():
        # Start Ollama server (add 'serve' argument if necessary)
        subprocess.Popen([path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Launching Ollama from: {path}")
    else:
        print("Ollama is already running.")

def list_models():
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"  # Endpoint for listing models
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        else:
            print(f"Failed to fetch models: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to Ollama server: {e}")
        return []

def ask_ollama(messages):
    url = f"{OLLAMA_BASE_URL}/api/generate"
    # Concatenate messages to create a prompt
    prompt = ""
    for msg in messages:
        role = msg['role']
        content = msg['content']
        prompt += f"{role.upper()}: {content}\n"
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            content = response.json()
            return content.get("response", "No response field in reply.")
        else:
            print(f"Generation error: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Ollama request error: {e}")
        return None


def ask_ollama_temperature(messages, temperature=0.5):
    url = f"{OLLAMA_BASE_URL}/api/generate"

    prompt = ""
    for msg in messages:
        role = msg['role']
        content = msg['content']
        prompt += f"{role.upper()}: {content}\n"
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            content = response.json()
            return content.get("response", "No response field in reply.")
        else:
            print(f"Generation error: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Ollama request error: {e}")
        return None



def main(path,qSpeech,temperature): 
    
    # Launch Text to Speech
    if qSpeech:
        launch_speech_if_needed()
        
    # Launch Ollama if it's not already running
    launch_ollama_if_needed()

    # Check if the model exists locally
    models = list_models()
    if MODEL_NAME not in models:
        print(f"Model {MODEL_NAME} not found locally. Available models: {models}")
        return

    # Initialize conversation with a system message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    # Create a file to save the conversation, using datetime in the filename
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ollama_conversation_{now_str}.txt"
    filename = path+"/"+filename
    
    with open(filename, "w", encoding="utf-8") as file:
        print("")
        print(f"Start chatting with {MODEL_NAME}. Type 'exit' to quit.")
        print("")
        while True:
            #user_input = input("You: ")
            user_input = input("👦: ")
            if user_input.lower() in ["exit", "quit", ""]:
                print("Ending conversation.")
                sys.exit()
                break
            
            if user_input.startswith("/temp "):
               try:
                   new_temp = float(user_input.split()[1])
                   if 0.0 <= new_temp <= 1.0:
                       temperature = new_temp
                       print(f"Update Temperature  {temperature}")
                   else:
                       print("Temperature must between 0 et 1.")
               except ValueError:
                   print("Temperature Format Unvalide")
               continue 
                 
            messages.append({"role": "user", "content": user_input})
            assistant_reply = ask_ollama_temperature(messages,temperature)
            if assistant_reply is None:
                print("No response received.")
                break
            messages.append({"role": "assistant", "content": assistant_reply})
            #print(f"Assistant: {assistant_reply}")
            
            print(f"🤖: {assistant_reply}")
            
            if qSpeech:
                play_speech(assistant_reply)

            file.write(f"You: {user_input}\n")
            file.write(f"Assistant: {assistant_reply}\n\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--Path', type=str, default='.', help='Path to directory containing conversation')
    parser.add_argument('--Model', type=str, default="qwen2.5-coder:7b", help='Model')
    parser.add_argument('--URL', type=str, default="http://localhost:11434", help='URL')
    parser.add_argument('--Speech', type=int, default=0, help='Speech on or off ')
    parser.add_argument('--Temperature', type=float, default=0.0, help='Temperature between 0.0 and 1.0 ')
    
    
    args = parser.parse_args()    
    MODEL_NAME =  args.Model
    OLLAMA_BASE_URL = args.URL
    
    if not os.path.exists(args.Path):
        os.makedirs(args.Path)
        
    main(args.Path,args.Speech,args.Temperature)

