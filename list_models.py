import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("GEMINI_API_KEY", "").strip()

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing.")

try:
    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=30000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    ) as client:
        print("Models supporting generateContent:", flush=True)

        for model in client.models.list():
            actions = model.supported_actions or []

            if "generateContent" in actions:
                print(model.name, flush=True)

except errors.APIError as error:
    print(f"API error: {error.code}")

except Exception as error:
    print(f"Error type: {type(error).__name__}")