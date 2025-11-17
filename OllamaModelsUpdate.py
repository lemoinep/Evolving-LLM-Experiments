# Author(s): Dr. Patrick Lemoine

import subprocess

def get_models():
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split("\n")
        models = [line.split()[0] for line in lines if line.strip()]
        return models
    except FileNotFoundError:
        print("Error: the 'ollama' command is not installed or could not be found.")
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error while retrieving the list of models : {e}")
        return []

def update_model(model):
    try:
        subprocess.run(
            ["ollama", "pull", model],
            check=True
        )
        print(f"Model '{model}' updated successfully.")
    except subprocess.CalledProcessError:
        print(f"Failed to update the model '{model}'.")

def main():
    models = get_models()
    if not models:
        print("No models to update.")
        return
    for model in models:
        update_model(model)

if __name__ == "__main__":
    main()
