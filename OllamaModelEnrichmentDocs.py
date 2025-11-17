# Author(s): Dr. Patrick Lemoine

import os
import sys
import ollama
import json
import subprocess
import psutil
import requests
from datetime import datetime
import PyPDF2
import re
import keyboard

JSON_PATH = "ollama_path.json"
OLLAMA_BASE_URL = "http://localhost:11434"

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
            return
    if not is_ollama_running():
        subprocess.Popen([path, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Launching Ollama from: {path}")
    else:
        print("Ollama is already running.")

def create_model_with_text(model_name: str, long_text: str, nb_tokens):
    system_prompt = f"You are an expert on the following text. Use it to answer questions:\n{long_text}"
    ollama.create(
        model=model_name,
        from_="qwen2.5-coder:7b",
        system=system_prompt,
        parameters={
            "temperature": 0.7,
            #"num_ctx": 4096
            "num_ctx":nb_tokens
        }
    )
    print(f"Model '{model_name}' created successfully.")

def ask_question(model_name: str, question: str):
    messages = [{"role": "user", "content": question}]
    try:
        print(f"Sending the question to model '{model_name}' : {question}")
        response = ollama.chat(model=model_name, messages=messages)
        print("Raw full response :", response)
        if isinstance(response, dict):
            content = response.get('message', {}).get('content')
            if content:
                print("\nModel's answer :\n", content)
            else:
                print("Unexpected format or 'content' field missing. Response :", response)
        else:
            print("Unexpected type for the response (not a dict) :", type(response))
    except Exception as e:
        print("Error while calling Ollama :", e)


def count_tokens_in_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return len(tokens)


def concat_txt_and_pdf_from_folder(folder_path):
    all_text = []
    selected_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith('.txt') or file.lower().endswith('.pdf'):
            selected_files.append(file)
    if not selected_files:
        print("No .txt or .pdf files found in the folder :", folder_path)
        return ""
    print("Files detected :", selected_files)
    for file in selected_files:
        full_path = os.path.join(folder_path, file)
        
        print(f"File : {full_path}")
        number_tokens = count_tokens_in_txt(full_path)
        print(f"Number of tokens : {number_tokens}")
        
        
        if file.lower().endswith('.txt'):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    all_text.append(f"\n===== {file} =====\n")
                    all_text.append(f.read())
            except Exception as e:
                print(f"Error reading TXT {file} : {e}")
        elif file.lower().endswith('.pdf'):
            try:
                with open(full_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    content = []
                    for page in pdf_reader.pages:
                        content.append(page.extract_text() or "")
                    all_text.append(f"\n===== {file} =====\n")
                    all_text.append("\n".join(content))
            except Exception as e:
                print(f"Error reading PDF {file} : {e}")
    return '\n'.join(all_text)



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

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--Path', type=str, default='.',
                        help='Folder containing .pdf and .txt files to load')
    parser.add_argument('--Model', type=str, default="qwen2.5-coder:7b", help='Name of the base model')
    parser.add_argument('--NameNewModel', type=str, default="long-text-expert-file", help='Name of the new model')
    args = parser.parse_args()

    folder_path = os.path.abspath(args.Path)
    NAME_NEW_MODEL = args.NameNewModel

    print("Source Folder =", folder_path)
    print("Name of New Model =", NAME_NEW_MODEL)
    
    

    FileData = concat_txt_and_pdf_from_folder(folder_path)
    
    number_tokens = len(re.findall(r"\w+|[^\w\s]", FileData, re.UNICODE))
    print(f"Number of tokens : {number_tokens}")


    if not FileData:
        print("No data loaded, stopping the program.")
        sys.exit(1)



    #print(FileData[:1000], "...")  

    launch_ollama_if_needed()
    
    models = list_models()
    
    create_model_with_text(NAME_NEW_MODEL, FileData, int(number_tokens*1.1))
    
    print("\n--- Test du modèle ---")
    ask_question(NAME_NEW_MODEL, "Hello.")
    print("\n--- Terminé ---")
    