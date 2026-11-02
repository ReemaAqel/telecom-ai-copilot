import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors


PROJECT_DIR = Path(__file__).resolve().parent

load_dotenv(PROJECT_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY", "").strip()

model_name = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest",
).strip()


def hide_key(value):
    """إخفاء المفتاح من أي رسالة قبل عرضها."""
    return str(value).replace(api_key, "[REDACTED]")


if not api_key:
    raise ValueError("GEMINI_API_KEY is missing.")

if not model_name:
    raise ValueError("GEMINI_MODEL is missing.")


print(f"Testing model: {model_name}", flush=True)
started = time.perf_counter()

try:
    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=60000,
            retry_options=types.HttpRetryOptions(
                attempts=1,
            ),
        ),
    ) as client:
        response = client.models.generate_content(
            model=model_name,
            contents="Reply with only: OK",
        )

        print("Answer:", response.text, flush=True)

except errors.APIError as error:
    print(f"Gemini error code: {error.code}")
    print(f"Error type: {type(error).__name__}")

    message = getattr(error, "message", None) or str(error)
    print("Message:", hide_key(message), flush=True)

except Exception as error:
    print(f"Error type: {type(error).__name__}")
    print("Message:", hide_key(error), flush=True)

finally:
    elapsed = time.perf_counter() - started
    print(f"Elapsed: {elapsed:.1f} seconds", flush=True)