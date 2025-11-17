# Author(s): Dr. Patrick Lemoine

import os
import json
import cv2
import base64
import requests
from datetime import datetime
import pyttsx3
import psutil
import subprocess
import time
import ollama

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2-vision"  
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
    for path_dir in os.getenv('PATH', '').split(os.pathsep):
        candidate = os.path.join(path_dir, "Ollama.exe")
        if os.path.isfile(candidate):
            return candidate
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



def encode_image_to_base64beta(image_path):
    if not os.path.isfile(image_path):
        print(f"Error: The file '{image_path}' could not be found.")
        return None
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    return base64.b64encode(img_bytes).decode("utf-8")


def encode_image_to_base64(image_path):
    if not os.path.isfile(image_path):
        print(f"Error: The file '{image_path}' could not be found..")
        return None
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    return base64.b64encode(img_bytes).decode()


def ask_ollama_with_image(messages, base64_image, base_url, model_name):
    url = f"{base_url}/api/chat"
    
    
    #print("base_url="+base_url)
    #print("url="+url)
    #print("model_name="+model_name)
    
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": messages,
            "images":  [base64_image]
        }
    ]
    
    data = {
        "model": model_name,
        "messages": prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    #if response.status_code == 500:
    if response.status_code == 500:
          content = response.json()
          if "choices" in content and len(content["choices"]) > 0:
              return content["choices"][0]["message"]["content"]
          else:
              return "No valid response from the model."
    else:
          return f"API error {response.status_code}: {response.text}"
    

def ask_ollama_with_image_temperature(messages, base64_image, base_url, model_name,temperature=0.5):
    url = f"{base_url}/api/chat"
    
    
    #print("base_url="+base_url)
    #print("url="+url)
    #print("model_name="+model_name)
    
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": messages,
            "images":  [base64_image]
        }
    ]
    
    data = {
        "model": model_name,
        "messages": prompt,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    response = requests.post(url, json=data)
    #if response.status_code == 500:
    if response.status_code == 500:
          content = response.json()
          if "choices" in content and len(content["choices"]) > 0:
              return content["choices"][0]["message"]["content"]
          else:
              return "No valid response from the model."
    else:
          return f"API error {response.status_code}: {response.text}"


def ask_ollama_with_image_optimized_New(messages, base64_image, model_name):
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": messages,
            "images": [base64_image]
        }
    ]

    options = {
        "temperature": 0.7,
        "max_tokens": 500, 
        "stream": False
    }

    response = ollama.chat(
        model=model_name,
        messages=prompt,
        options=options
    )

    if response and "choices" in response and len(response["choices"]) > 0:
        return response["choices"][0]["message"]["content"]
    else:
        return "No valid response from the model."


def ask_ollama_with_image2(messages, image_path, base_url, model_name):

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    url = f"{base_url}/api/chat"
    
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": messages,
            "images": [base64_image]
        }
    ]
    
    data = {
        "model": model_name,
        "messages": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=data, timeout=120)
        if response.status_code == 200:
            content = response.json()
            print("Full API response:", content)
            if "choices" in content and len(content["choices"]) > 0:
                return content["choices"][0]["message"]["content"]
            elif "message" in content:
                return content["message"].get("content", "Empty message content.")
            else:
                return "No response choices found in the API reply."
        else:
            return f"API error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Unexpected error: {e}"





def ask_ollama_with_text(messages, base_url, model_name):
    url = f"{base_url}/api/chat"
    data = {"model": model_name, "messages": messages}
    try:
        r = requests.post(url, json=data, timeout=120)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Erreur HTTP {r.status_code} : {r.text}")
    except Exception as e:
        print(f"Erreur lors de la requête : {e}")
    return None


def ask_ollama(messages):
    url = f"{OLLAMA_BASE_URL}/api/generate"

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

def launch_speech_if_needed():
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', int(rate))
    volume = engine.getProperty('volume')
    engine.setProperty('volume', float(volume))
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    return engine

def play_speech(engine, text):
    engine.say(text)
    engine.runAndWait()


def show_and_save_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Unable to read image '{image_path}'.")
        return
    cv2.imshow("Original image", img)
    #save_path = "image_envoyee.jpg"
    #cv2.imwrite(save_path, img)
    #print(f"L’image envoyée a été sauvegardée sous {save_path}")
    cv2.waitKey(0)
    cv2.destroyAllWindows()



def extraire_contenu(json_string):
    json_string = json_string.split(": {")[1].rstrip()
    json_string = "{" + json_string
    data = json.loads(json_string)
    contenu = data["message"]["content"]
    
    return contenu

def main(path,qSpeech,img_path,temperature): 
    
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
    
    
    #○print("Path Image: "+img_path)
    base64image = encode_image_to_base64(img_path)
    if base64image is None:
        return
    #show_and_save_image(img_path)
    

    # Initialize conversation with a system message
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    # Create a file to save the conversation, using datetime in the filename
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ollama_conversation_{now_str}.txt"
    filename = path+"/"+filename
    

    user_input = "Hello"
    messages.append({"role": "user", "content": user_input})
    assistant_reply = ask_ollama(messages)
    if assistant_reply is None:
        print("No response received.")
    messages.append({"role": "assistant", "content": assistant_reply})
    #print(f"Assistant: {assistant_reply}")
    
    print("")
    print("")
    print(f"🤖: {assistant_reply}")


    user_input = "Can you make a description of my picture ?"
 
    print(f"👦:  {user_input}\n")
    
    
    result = ask_ollama_with_image_temperature(user_input, base64image, OLLAMA_BASE_URL,MODEL_NAME,temperature)
    
    result = extraire_contenu(result)


    if result is None:
        print("Initial error during image request.")
        return
    messages.append({"role": "assistant", "content": result})
    print(f"🤖: {result}\n\n")
    
    with open(filename, "w", encoding="utf-8") as file:        
        file.write(f"You: {user_input}\n")
        file.write(f"Assistant: {result}\n\n")        
            
        while True:
            #user_input = input("You: ")
            user_input = input("👦: ")
            if user_input.lower() in ["exit", "quit", ""]:
                print("Ending conversation.")
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
            assistant_reply = ask_ollama_with_image_temperature(user_input, base64image, OLLAMA_BASE_URL,MODEL_NAME,temperature)
            assistant_reply = extraire_contenu(assistant_reply)
            
            
            if assistant_reply is None:
                print("No response received.")
                break
            messages.append({"role": "assistant", "content": assistant_reply})

            print(f"🤖: {assistant_reply}")
            
            if qSpeech:
                play_speech(assistant_reply)

            file.write(f"You: {user_input}\n")
            file.write(f"Assistant: {assistant_reply}\n\n")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()    
    parser.add_argument('--Path', type=str, default='.', help='Directory to save the conversation')
    parser.add_argument('--Model', type=str, default="llama3.2-vision", help='Name of the Ollama model')
    parser.add_argument('--URL', type=str, default="http://localhost:11434", help='URL of the Ollama server')
    parser.add_argument('--Image', type=str, required=True, help='Path to the .JPG image file')
    parser.add_argument('--Speech', type=int, default=0, help='Text-to-speech (1=yes, 0=no)')
    parser.add_argument('--Temperature', type=float, default=0.0, help='Temperature between 0.0 and 1.0')


    args = parser.parse_args()

    image_path = args.Image
    if not os.path.isabs(image_path):
        image_path = os.path.join(args.Path, args.Image)
    if not os.path.exists(args.Path):
        os.makedirs(args.Path, exist_ok=True)
        
    MODEL_NAME =  args.Model
    OLLAMA_BASE_URL = args.URL
    
    image_path = args.Path+"/"+args.Image
    
    main(args.Path,args.Speech,image_path,args.Temperature)
