# Author(s): Dr. Patrick Lemoine

import os
import sys
import ollama
import json
import subprocess
import psutil
import requests
from datetime import datetime
import fitz  
from PIL import Image
import base64

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llava" 
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



def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

def extract_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    images_base64 = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Convertir en base64
            b64_str = base64.b64encode(image_bytes).decode()
            images_base64.append(b64_str)
    return images_base64

def ask_ollama_with_text_and_images(text, images_base64, base_url, model_name):
    url = f"{base_url}/api/chat"
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": text,
            "images": images_base64
        }
    ]
    data = {
        "model": model_name,
        "messages": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        content = response.json()
        if "choices" in content and len(content["choices"]) > 0:
            return content["choices"][0]["message"]["content"]
        else:
            return "No valid response from the model."
    else:
        return f"API error {response.status_code}: {response.text}"



def parent_path(path):
    return os.path.dirname(path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--Path', type=str, default='.', help='Path to directory containing conversation')
    parser.add_argument('--Model', type=str, default="llava", help='Model') # Multimodal model vision+text
    parser.add_argument('--URL', type=str, default="http://localhost:11434", help='Ollama server URL')
    parser.add_argument('--InputDataPDF', type=str, default="InputData.pdf", help='Input PDF data')
    
    args = parser.parse_args()
      
    input_up_folder = parent_path(args.Path)   
    pdf_file = input_up_folder+"/"+args.InputData
    print("INPUT_DATA="+pdf_file)
    
    pdf_text = extract_text_from_pdf(pdf_file)
    print("Extracted text from PDF (first 500 characters):")
    print(pdf_text[:500] + "...\n")
    
    images_b64 = extract_images_from_pdf(pdf_file)
    print(f"{len(images_b64)} images extracted and encoded in base64.")
    
    MODEL_NAME = args.Model
    OLLAMA_BASE_URL = args.URL

    answer = ask_ollama_with_text_and_images(pdf_text, images_b64, OLLAMA_BASE_URL, MODEL_NAME)
    print("\nOllama model's response :")
    print(answer)
