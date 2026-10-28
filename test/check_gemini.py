
import os

from dotenv import load_dotenv
from openai import OpenAI, APIStatusError, APIConnectionError

load_dotenv()

api_key = os.getenv("MACY_LLM_API_KEY", "")
model = os.getenv("MACY_LLM_MODEL", "")
base_url = os.getenv("MACY_LLM_BASE_URL", "")

print("=== MACY AI GEMINI TEST ===")
print("API key present:", bool(api_key and not api_key.startswith("PASTE_")))
print("Model:", model)
print("Base URL:", base_url)

if not api_key or api_key.startswith("PASTE_"):
    raise SystemExit("Configure MACY_LLM_API_KEY in .env first.")

if not model or not base_url:
    raise SystemExit("Model or base URL is missing.")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=30.0,
    max_retries=0,
)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Write one short sentence about artificial intelligence."
            }
        ],
        max_tokens=150,
    )

    print("\nSUCCESS: Gemini responded.")
    print("Response:", response.choices[0].message.content)

except APIStatusError as error:
    print("\nGemini API returned an error.")
    print("HTTP status:", error.status_code)
    print("Error type:", type(error).__name__)

except APIConnectionError as error:
    print("\nConnection failed.")
    print("Error type:", type(error).__name__)

except Exception as error:
    print("\nUnexpected error.")
    print("Error type:", type(error).__name__)
