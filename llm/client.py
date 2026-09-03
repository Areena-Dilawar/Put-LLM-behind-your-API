import os

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "llama3.2:3b",
)

TIMEOUT_SECONDS = int(
    os.getenv("LLM_TIMEOUT_SECONDS", "60")
)


def generate_response(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
        },
        timeout=TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]