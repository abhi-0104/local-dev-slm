import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"

def check_ollama_health() -> bool:
    """Checks if the Ollama app is actually running."""
    try:
        response = requests.get("http://localhost:11434/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def generate_text(prompt: str, model: str = "llama3.2:3b", system_prompt: str = "", temperature: float = 0.0, require_json: bool = False) -> str:
    """Sends a prompt to the local Ollama model and returns the text response."""
    
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,  
        "options": {
            "temperature": temperature 
        }
    }
    
    # NEW: If we require JSON, tell Ollama to force the AI into JSON mode!
    if require_json:
        payload["format"] = "json"
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status() 
        
        result = response.json()
        return result.get("response", "")
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return f"Error: Could not generate text."