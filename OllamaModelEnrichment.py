# Author(s): Dr. Patrick Lemoine

import os
import sys
import ollama
import json
import subprocess
import psutil
import requests
from datetime import datetime
import keyboard

OLLAMA_BASE_URL = "http://localhost:11434"
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


def create_model_with_text(model_name: str, long_text: str):
    system_prompt = f"You are an expert on the following text. Use it to answer questions:\n{long_text}"
    ollama.create(
        model=model_name,
        from_="qwen2.5-coder:7b",
        system=system_prompt,
        parameters={
            "temperature": 0.7,
            "num_ctx": 4096
            #"num_ctx": 8192
            #"num_ctx":  9000
        }
    )
    print(f"Model '{model_name}' created successfully.")

def ask_question(model_name: str, question: str):
    messages = [{"role": "user", "content": question}]
    response = ollama.chat(model=model_name, messages=messages)
    print("Réponse :", response['message']['content'])


def parent_path(path):
    return os.path.dirname(path)


def list_models():
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"  
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


def list_models():
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags" 
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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--Path', type=str, default='.', help='Path to directory containing conversation')
    parser.add_argument('--Model', type=str, default="qwen2.5-coder:7b", help='Model')
    
    parser.add_argument('--InputData', type=str, default="InputData.txt", help='InputData')
    parser.add_argument('--NameNewModel', type=str, default="long-text-expert-file", help='NameNewModel')
    
    args = parser.parse_args()
    
    
    input_up_folder = parent_path(args.Path)
    
    INPUT_DATA = input_up_folder+"/"+args.InputData
    NAME_NEW_MODEL = args.NameNewModel
    
    print("INPUT_DATA="+INPUT_DATA)
    print("NAME_NEW_MODEL="+NAME_NEW_MODEL)
    

    with open(INPUT_DATA, "r", encoding="utf-8") as f:
        FileData = f.read()
        
    print(FileData) 
    # Launch Ollama if it's not already running
    launch_ollama_if_needed()
    
    # Check if the model exists locally
    models = list_models()
    #if MODEL_NAME not in models:
    #    print(f"Model {MODEL_NAME} not found locally. Available models: {models}")
    #    return
    
    
    create_model_with_text(NAME_NEW_MODEL, FileData)
    
    ask_question(NAME_NEW_MODEL, "Hello ")
    
    print("Press ESC to continue...")
    keyboard.wait('esc')

    print("Continue the program...")

