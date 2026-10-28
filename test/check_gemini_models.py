
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, APIStatusError, APIConnectionError

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

api_key = os.getenv("MACY_LLM_API_KEY", "")
model_name = os.getenv("MACY_LLM_MODEL", "")
base_url = os.getenv("MACY_LLM_BASE_URL", "")

print("\n=== MACY AI GEMINI MODEL CHECK ===")

if not api_key or api_key.startswith("PASTE_"):
    raise SystemExit("Gemini API key is not configured.")

if not model_name or not base_url:
    raise SystemExit("Model or base URL is missing.")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=30.0,
    max_retries=0,
)

try:
    models = client.models.list()

    # Normalize the 'models/' prefix.
    available = sorted({
        item.id.removeprefix("models/")
        for item in models
    })

    configured = model_name.removeprefix("models/")

    print("Configured model:", configured)
    print("Model listed:", configured in available)

    print("\nAvailable Flash text-model candidates:")

    candidates = [
        name for name in available
        if "flash" in name.lower()
        and "image" not in name.lower()
        and "tts" not in name.lower()
        and "live" not in name.lower()
        and "embedding" not in name.lower()
    ]

    for name in candidates:
        print(" -", name)

    print("\nChecking configured model...")

    response = client.chat.completions.create(
        model=configured,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: Macy AI connected"
            }
        ],
        max_tokens=100,
    )

    answer = response.choices[0].message.content

    print("\nSUCCESS: Gemini returned a response.")
    print("Answer:", answer)

except APIStatusError as error:
    print("\nGEMINI API ERROR")
    print("HTTP status:", error.status_code)
    print("Error type:", type(error).__name__)

except APIConnectionError:
    print("\nNETWORK ERROR: Could not reach Gemini.")

except Exception as error:
    print("\nOTHER ERROR:", type(error).__name__)
