# Author(s): Dr. Patrick Lemoine, enhanced multi-file PDF/TXT/Image with advanced diagnostics

import os
import sys
import ollama
import json
import subprocess
import psutil
import requests
from datetime import datetime
import PyPDF2
import base64

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

def encode_image_to_base64(image_path):
    try:
        with open(image_path, 'rb') as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def concat_txt_pdf_and_images_from_folder(folder_path):
    all_text = []
    selected_files = []
    image_data_list = []
    
    for file in os.listdir(folder_path):
        ext = file.lower().split('.')[-1]
        if ext in ['txt', 'pdf', 'jpg', 'jpeg', 'png', 'bmp']:
            selected_files.append(file)
    if not selected_files:
        print("No .txt, .pdf, or image files found in folder:", folder_path)
        return "", []
    print("Detected files:", selected_files)

    for file in selected_files:
        full_path = os.path.join(folder_path, file)
        ext = file.lower().split('.')[-1]
        if ext == 'txt':
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    all_text.append(f"\n===== {file} =====\n")
                    all_text.append(f.read())
            except Exception as e:
                print(f"TXT reading error {file}: {e}")
        elif ext == 'pdf':
            try:
                with open(full_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    content = []
                    for page in pdf_reader.pages:
                        content.append(page.extract_text() or "")
                    all_text.append(f"\n===== {file} =====\n")
                    all_text.append("\n".join(content))
            except Exception as e:
                print(f"PDF reading error {file}: {e}")
        elif ext in ['jpg', 'jpeg', 'png', 'bmp']:
            encoded_img = encode_image_to_base64(full_path)
            if encoded_img:
                image_data_list.append((file, encoded_img))
            else:
                print(f"Skipping image {file} due to encoding error.")
    return '\n'.join(all_text), image_data_list

def create_model_with_text_and_images(model_name: str, long_text: str, images_base64: list):
    system_prompt = f"You are an expert on the following text. Use it to answer questions:\n{long_text}"
    images = [img_b64 for (_, img_b64) in images_base64]
    ollama.create(
        model=model_name,
        from_="qwen2.5-coder:7b",
        system=system_prompt,
        parameters={
            "temperature": 0.7,
            #"num_ctx": 4096
            "num_ctx": 8192
        }
    )
    print(f"Model '{model_name}' created successfully.")

def ask_question_with_images(model_name: str, question: str, images_base64: list):
    message = {
        "role": "user",
        "content": question,
    }
    if images_base64:
        message["images"] = [img_b64 for (_, img_b64) in images_base64]

    messages = [message]
    try:
        print(f"Sending question to the model '{model_name}': {question}")
        response = ollama.chat(model=model_name, messages=messages)
        print("Full raw response:", response)
        if isinstance(response, dict):
            content = response.get('message', {}).get('content')
            if content:
                print("\nModel response:\n", content)
            else:
                print("Unexpected format or missing 'content' field. Response:", response)
        else:
            print("Unexpected type for response (not a dict):", type(response))
    except Exception as e:
        print("Error during Ollama call:", e)


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
                        help='Folder containing .pdf, .txt, and image files to load')
    parser.add_argument('--Model', type=str, default="qwen2.5-coder:7b", help='Base model name')
    parser.add_argument('--NameNewModel', type=str, default="long-text-expert-file", help='Name of the new model')
    args = parser.parse_args()

    folder_path = os.path.abspath(args.Path)
    NAME_NEW_MODEL = args.NameNewModel

    print("Source folder =", folder_path)
    print("New model name =", NAME_NEW_MODEL)

    FileTextData, FileImagesData = concat_txt_pdf_and_images_from_folder(folder_path)
    if not FileTextData and not FileImagesData:
        print("No data loaded (text or images), stopping program.")
        sys.exit(1)

    print("\n--- First excerpt of the loaded corpus ---")
    if FileTextData:
        print(FileTextData[:1000], "...")  # Show 1000 characters from text corpus
    else:
        print("No text files loaded.")

    if FileImagesData:
        print(f"{len(FileImagesData)} image(s) loaded: {[name for (name, _) in FileImagesData]}")
    else:
        print("No images loaded.")

    launch_ollama_if_needed()
    
    models = list_models()
    
    create_model_with_text_and_images(NAME_NEW_MODEL, FileTextData, FileImagesData)

    print("\n--- Testing the model ---")
    ask_question_with_images(NAME_NEW_MODEL, "Hello! Please summarize this corpus.", FileImagesData)
    print("\n--- Finished ---")
