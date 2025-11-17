# Author(s): Dr. Patrick Lemoine

import os
import sys
import ollama
import json
import subprocess
import psutil
import requests
from datetime import datetime
import re
import keyboard
import sqlite3

from langdetect import detect, DetectorFactory
import yake
import pke
import spacy
from nltk.corpus import stopwords

import socket

import wikipedia
from spellchecker import SpellChecker
from textblob import TextBlob
import json


DetectorFactory.seed = 0 



SUPPORTED_LANGS = ['fr', 'en', 'es', 'de']

SPACY_MODELS = {
    'fr': 'fr_core_news_sm',
    'en': 'en_core_web_sm',
    #'it': 'it_core_web_sm',
    'es': 'es_core_news_sm',
    #'pt': 'pt_core_news_sm',
    'de': 'de_core_news_sm'
}

STOPWORDS_LANGS = {
    'fr': 'french',
    'en': 'english',
    #'it': 'italian',
    'es': 'spanish',
    #'pt': 'portuguese',
    'de': 'german'
}


# WIKI PART

def robust_spell_correct(text):
    spell = SpellChecker()
    corrected_words = []
    for word in text.split():
        correction = spell.correction(word)
        corrected_words.append(correction if correction else word)
    corrected = ' '.join(corrected_words)
    blob = TextBlob(corrected)
    fully_corrected = str(blob.correct())
    return fully_corrected

def parent_path(path):
    return os.path.dirname(os.path.abspath(path))

def save_first_image(img_url, page_title, output_folder):
    if not img_url:
        return None
    try:
        images_folder = os.path.join(output_folder, "Images")
        os.makedirs(images_folder, exist_ok=True)
        ext = os.path.splitext(img_url)[-1].split("?")[0]
        if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".svg"]:
            ext = ".jpg"
        safe_title = "".join(c for c in page_title if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{safe_title}_first_image{ext}"
        img_path = os.path.join(images_folder, filename)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/58.0.3029.110 Safari/537.36"
            )
        }
        response = requests.get(img_url, timeout=10, headers=headers)
        response.raise_for_status()
        with open(img_path, "wb") as img_file:
            img_file.write(response.content)
        print(f"[Info] Image saved: {img_path}")
        return img_path
    except Exception as e:
        print(f"[Warning] Could not save image: {e}")
        return None


def main_all_information(base_path, sentences, user_input):
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = os.path.abspath(base_path)
    output_dir = os.path.join(parent_path(base_path), "Request_Response")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"wikipedia_conversation_{datetime_str}.txt"
    filepath = os.path.join(output_dir, filename)

    wikipedia.set_lang("en")
    print("=== Wikipedia Query ===")
    #user_input = input("👦: ").strip()
    print(f"User query: {user_input}")
    
    
    corrected = robust_spell_correct(user_input)
    print(f"robust_spell_correct: {corrected}")
    

    print("********************************************************************")

    results = []
    results_json = {}
    try:
        search_results = wikipedia.search(user_input)
        print("--------------------------------------------------------------------")
        print("Search Results"+str(search_results))
        print("--------------------------------------------------------------------")
            
        if not search_results:
            results.append(f"No results found for '{user_input}'.")
            results_json['error'] = f"No results found for '{user_input}'."
        else:
            page_title = search_results[0]  # Best match found
            print(f"Best match: {page_title}")
            try:
                page = wikipedia.page(page_title, auto_suggest=False)
                summary = wikipedia.summary(page_title, sentences=sentences, auto_suggest=False)
                first_image_url = page.images[0] if page.images else ""
                first_img_path = save_first_image(first_image_url, page_title, output_dir) if first_image_url else None
                all_images = page.images
                all_links = page.links
                sections = page.sections if hasattr(page, "sections") else "Not available (use wikipediaapi for section tree)"
                categories = page.categories if hasattr(page, "categories") else "Not available in wikipedia module"

                # Assemble results
                results = [
                    f"Summary:\n{summary}",
                    f"\nTitle: {page.title}",
                    f"\nURL: {page.url}",
                    f"\nContent:\n{page.content}",  # Full content
                    f"\nFirst image URL: {first_image_url or 'No image found'}",
                    f"\nFirst image saved at: {first_img_path or 'None'}",
                    f"\nAll images: {all_images if all_images else 'No images'}",
                    f"\nAll internal links: {all_links if all_links else 'No links'}",
                    f"\nSections (basic): {sections}",
                    f"\nCategories (basic): {categories}"
                ]
                results_json = {
                   "summary": summary,
                   "title": page.title,
                   "url": page.url,
                   "content": page.content,
                   "first_image_url": first_image_url or None,
                   "first_image_saved_at": first_img_path or None,
                   "all_images": all_images if all_images else [],
                   "all_internal_links": all_links if all_links else []
               }
            except wikipedia.exceptions.DisambiguationError as e:
                results = [
                    f"[Error] Ambiguous term '{page_title}'. Possible suggestions:",
                    ', '.join(e.options)
                ]
                results_json = {
                    "error": f"Ambiguous term '{page_title}'. Suggestions",
                    "suggestions": list(e.options)
                }
            except wikipedia.exceptions.PageError as e:
                results = [f"[Page error] {e}"]
                results_json = {"error": str(e)}
            except Exception as e:
                results = [f"[Unknown error] {str(e)}"]
                results_json = {"error": str(e)}
    except Exception as e:
        results = [f"[Unknown error] {str(e)}"]

    with open(filepath, "w", encoding="utf-8") as f:
        for block in results:
            f.write(block + "\n\n")
            
    # Sauvegarde JSON
    json_path = filepath.replace('.txt', '.json')
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(results_json, f_json, ensure_ascii=False, indent=2)

    #print("\n🤖:")
    #for block in results:
    #    print(block)
    print(f"\nJSON saved to: {json_path}")



# INTERNET CONNECTION PART

def internet_connection_1(url="https://www.google.com", timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def internet_connection_2(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False
        
        
# OLLAMA PART

def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return None

def extract_yake(text, language):
    extractor = yake.KeywordExtractor(lan=language, n=3, top=10)
    keywords = extractor.extract_keywords(text)
    return [kw for kw, score in keywords]

def extract_pke(text, language):
    if language not in SPACY_MODELS:
        raise ValueError(f"Language not supported: {language}")
    nlp = spacy.load(SPACY_MODELS[language])
    extractor = pke.unsupervised.MultipartiteRank()
    extractor.load_document(input=text, language=language, spacy_model=nlp)
    stoplist_lang = STOPWORDS_LANGS.get(language, 'english')
    extractor.stoplist = stopwords.words(stoplist_lang)
    extractor.candidate_selection()
    extractor.candidate_weighting()
    keyphrases = extractor.get_n_best(n=10)
    return [kw for kw, score in keyphrases]

def extract_keywords(text):
    language = detect_language(text)
    if language not in SUPPORTED_LANGS:
        raise ValueError(f"Detected language not supported: {language}")
    print("Detected language:", language)
    print("YAKE keywords:", extract_yake(text, language))
    print("PKE keywords:", extract_pke(text, language))

def extract_person_names(text):
    language = detect_language(text)
    if language not in SPACY_MODELS:
        raise ValueError(f"Language '{language}' not supported")
    nlp = spacy.load(SPACY_MODELS[language])
    doc = nlp(text)
    labels = ["PER", "PERSON"]
    names = [ent.text for ent in doc.ents if ent.label_ in labels]
    return names


def extract_person_names2(text):
    names = []
    for language in SUPPORTED_LANGS:
        #if is_person_query(text, language):
            #print("QUERY")
            nlp = spacy.load(SPACY_MODELS[language])
            doc = nlp(text)
            labels = ["PER", "PERSON"]
            names_sub = [ent.text for ent in doc.ents if ent.label_ in labels]
            if names_sub:
                 names = names_sub
    return names

QUESTION_PATTERNS = {
    'fr': ['donne moi des informations concernant', 'qui est', 'informations sur', 'parle moi de', 'qui sont'],
    'en': ['give information about', 'who is', 'tell me about', 'information on', 'who are'],
    #'it': ['dammi informazioni su', 'chi è', 'informazioni su', 'parlami di', 'chi sono'],
    'es': ['dame información sobre', 'quién es', 'información sobre', 'háblame de', 'quiénes son'],
    #'pt': ['dê-me informações sobre', 'quem é', 'informações sobre', 'fale-me sobre', 'quem são'],
    'de': ['gib mir informationen über', 'wer ist', 'informationen über', 'erzähl mir von', 'wer sind']
}

def is_person_query(text, language):
    patterns = QUESTION_PATTERNS.get(language, [])
    text_lower = text.lower()
    for pattern in patterns:
        if pattern in text_lower:
            return True
    return False

def extract_person_keyword(text):
    language = detect_language(text)
    if language not in SUPPORTED_LANGS:
        return []
    if not is_person_query(text, language):
        return []
    nlp = spacy.load(SPACY_MODELS[language])
    doc = nlp(text)
    labels = ["PERSON", "PER"]
    person_names = [ent.text for ent in doc.ents if ent.label_ in labels]
    return person_names




# ---- Gestion SQLite pour keywords ---------------------
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recherches (
            keywords TEXT PRIMARY KEY,
            result TEXT
        )
    ''')
    conn.commit()
    conn.close()

def query_db(db_path, keywords):
    key = "_".join(sorted(set(keywords))).lower()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT result FROM recherches WHERE keywords=?', (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def insert_db(db_path, keywords, results):
    key = "_".join(sorted(set(keywords))).lower()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO recherches (keywords, result) VALUES (?, ?)', (key, json.dumps(results)))
    conn.commit()
    conn.close()

def recherche_fichiers_keywords_sqlite(path, keywords, db_path="resultats.db"):
    db_path = path+"/"+db_path
    init_db(db_path)
    result = query_db(db_path, keywords)
    if result is not None:
        print("Query found in SQLite database.")
        return result
    print("Searching .txt files in folder...")
    result_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.txt'):
                chemin = os.path.join(root, file)
                try:
                    with open(chemin, "r", encoding="utf-8") as f:
                        contenu = f.read().lower()
                    if all(k.lower() in contenu for k in keywords):
                        result_paths.append(chemin)
                except Exception as e:
                    print(f"Error path {chemin}: {e}")
    insert_db(db_path, keywords, result_paths)
    return result_paths

# ---- Logique Ollama ----------------------------------
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
    min_tokens = 4096
    ctx_tokens = max(nb_tokens, min_tokens)
    system_prompt = (
        "You are an expert assistant. "
        "Respond ONLY using the following text as your knowledge source. "
        "Do not invent information, do not use external knowledge. "
        "Strictly base all answers on this text:\n"
        f"{long_text}"
    )
    ollama.create(
        model=model_name,
        from_="qwen2.5-coder:7b",
        system=system_prompt,
        parameters={
            "temperature": 0.7,
            "num_ctx": ctx_tokens
        }
    )
    print(f"Model '{model_name}' created successfully (num_ctx={ctx_tokens}).")

def count_tokens_in_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()
    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)
    return len(tokens)

def extraire_keywords(phrase):
    return re.findall(r'\[(.*?)\]', phrase)

def save_interaction_json(path, interaction,datetime_str):
    filename = f"ollama_conversation_{datetime_str}.json"
    #filepath = os.path.join(path, "questions_reponses.json")
    filepath = os.path.join(path,filename)
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        data.append(interaction)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"JSON writing error: {e}")

def ask_and_save(model_name, path):
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    up_path = parent_path(path)
    up_path_output = up_path+"/Request_Response"
    if not os.path.exists(up_path_output):
        os.makedirs(up_path_output)
        
    while True:
        print("")
        question = input("👦: ")
        if question.strip().lower() == "exit":
            print("\nEnding conversation.")
            sys.exit()
            break

        date_question = datetime.now().isoformat()
        try:
            messages = [{"role": "user", "content": question}]
            response = ollama.chat(model=model_name, messages=messages)
            if hasattr(response, 'message'):
                content = getattr(response.message, 'content', None)
            elif isinstance(response, dict):
                content = response.get('message', {}).get('content')
            else:
                content = None
            if content:
                print("\n🤖:", content)
                date_reponse = datetime.now().isoformat()
                interaction = {
                    "question": question,
                    "date_question": date_question,
                    "reponse": content,
                    "date_reponse": date_reponse
                }
                save_interaction_json(up_path_output, interaction, datetime_str)
                print("\n")
            else:
                print("Response received but content empty or inaccessible.\n")
        except Exception as e:
            print("Error calling Ollama :", e)


def ask_and_save_beta(model_name, path, question):
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    up_path = parent_path(path)
    up_path_output = up_path+"/Request_Response"
    if not os.path.exists(up_path_output):
        os.makedirs(up_path_output)
        
    qQuestionNext = False
        
    while True:
        
        if qQuestionNext:
            print("")
            question = input("👦: ")
            if question.strip().lower() == "exit":
                print("\nEnding conversation.")
                sys.exit()
                break
            
        qQuestionNext = True            

        date_question = datetime.now().isoformat()
        try:
            messages = [{"role": "user", "content": question}]
            response = ollama.chat(model=model_name, messages=messages)
            if hasattr(response, 'message'):
                content = getattr(response.message, 'content', None)
            elif isinstance(response, dict):
                content = response.get('message', {}).get('content')
            else:
                content = None
            if content:
                print("\n🤖:", content)
                date_reponse = datetime.now().isoformat()
                interaction = {
                    "question": question,
                    "date_question": date_question,
                    "reponse": content,
                    "date_reponse": date_reponse
                }
                save_interaction_json(up_path_output, interaction, datetime_str)
                print("\n")
            else:
                print("Response received but content empty or inaccessible.\n")
        except Exception as e:
            print("Error calling Ollama :", e)


def parent_path(path):
    return os.path.dirname(path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--Path', type=str, default='.', help='Path')
    parser.add_argument('--Model', type=str, default="qwen2.5-coder:7b", help='Model')
    parser.add_argument('--NameNewModel', type=str, default="long-text-expert-file", help='Name New Model')
    
    sentences=1000
    
    args = parser.parse_args()

    folder_path = os.path.abspath(args.Path)
    
    question = input("👦: ")
    
    #keywords = extraire_keywords(question)
    
    
    #keywords = extract_person_keyword(question)
    keywords = extract_person_names2(question)
    
    size_keywords_list = len(keywords)
        
        
    NAME_NEW_MODEL = args.NameNewModel
    
    print("Source file =", folder_path)
    print("Basic model =", args.Model)
    print("Keywords :", keywords)

    launch_ollama_if_needed()

    print("Size Keywords ="+str(size_keywords_list))
    
    resultats = []
    if size_keywords_list>0:
        resultats = recherche_fichiers_keywords_sqlite(folder_path, keywords)
        
    if (not resultats and internet_connection_2()):
        main_all_information(folder_path, sentences, keywords[0])
        if size_keywords_list>0:
            resultats = recherche_fichiers_keywords_sqlite(folder_path, keywords)
        
    
    if resultats:
        print("Files found :", resultats)
        for i, filepath in enumerate(resultats):
            nombre_tokens = count_tokens_in_txt(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                long_text = f.read()
            model_name = f"{NAME_NEW_MODEL}_{i+1}"
            create_model_with_text(model_name, long_text, nombre_tokens)
            #ask_and_save(model_name, folder_path)
            ask_and_save_beta(model_name, folder_path, question)
    else:
        print("No file contains all keywords.")

    print("\n--- Close ---")
