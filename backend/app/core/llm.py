import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

def classify_transaction(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=30
    )

    return response.json()["response"].strip()
