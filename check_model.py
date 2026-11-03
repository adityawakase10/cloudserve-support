# Drafted with Claude (Anthropic), reviewed by Aditya Wakase
"""Smoke test: can we reach the model provider using the key in .env?"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()  # copies the lines in .env into environment variables

api_key = os.environ["GROQ_API_KEY"]  # crashes loudly if missing, which is what we want
model = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the word ready."}],
    },
    timeout=30,
)

print("status:", response.status_code)
if response.ok:
    print("reply:", response.json()["choices"][0]["message"]["content"])
else:
    print("error:", response.text)