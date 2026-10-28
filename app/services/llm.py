"""Macy AI: real AI script generation through an OpenAI-compatible API.

This service reads credentials from the backend's .env, not the Streamlit UI.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class AIConfigurationError(Exception):
    """The backend has no valid AI provider configuration."""


class AIGenerationError(Exception):
    """The provider could not generate a usable script."""


def _parse_result(raw_text: str) -> tuple[str, list[str]]:
    """Validate the provider's JSON response before returning it to the UI."""
    raw_text = raw_text.strip()
    # Some models wrap JSON in Markdown; extract the outer JSON object.
    opening, closing = raw_text.find("{"), raw_text.rfind("}")
    if opening < 0 or closing < opening:
        raise AIGenerationError("AI did not return JSON. Please try again.")

    try:
        data = json.loads(raw_text[opening : closing + 1])
    except json.JSONDecodeError as exc:
        raise AIGenerationError("AI returned invalid JSON. Please try again.") from exc

    if not isinstance(data, dict):
        raise AIGenerationError("AI returned an unexpected result.")

    script = data.get("script")
    keywords = data.get("keywords")
    if not isinstance(script, str) or not script.strip():
        raise AIGenerationError("AI did not return a video script.")
    if not isinstance(keywords, list) or not all(
        isinstance(word, str) for word in keywords
    ):
        raise AIGenerationError("AI did not return a keyword list.")

    cleaned: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        item = keyword.strip()
        if item and item.casefold() not in seen:
            cleaned.append(item)
            seen.add(item.casefold())
        if len(cleaned) >= 8:
            break
    if not cleaned:
        raise AIGenerationError("AI returned an empty keyword list.")

    return script.strip(), cleaned


def generate_ai_script(
    subject: str,
    language: str = "Auto Detect",
    paragraph_count: int = 3,
    custom_prompt: str = "",
) -> dict:
    """Generate a script and stock-footage search terms using a live provider."""
    api_key = os.getenv("MACY_LLM_API_KEY", "").strip()
    model = os.getenv("MACY_LLM_MODEL", "").strip()
    base_url = os.getenv("MACY_LLM_BASE_URL", "").strip()

    if not api_key:
        raise AIConfigurationError("MACY_LLM_API_KEY is missing from backend .env.")
    if not model:
        raise AIConfigurationError("MACY_LLM_MODEL is missing from backend .env.")

    client_options = {
        "api_key": api_key,
        "timeout": 60.0,
        "max_retries": 0,  # avoid surprise duplicate/billed calls while learning
    }
    if base_url:
        client_options["base_url"] = base_url

    system_prompt = (
        "You write engaging, accurate scripts for short narrated videos. "
        "Reply ONLY with a valid JSON object with exactly two keys: "
        "'script' (a string) and 'keywords' (an array of 4 to 8 short English "
        "search phrases suitable for stock video footage). "
        "Do not use Markdown code fences. Write the script in the requested language. "
        "Use exactly the requested number of short paragraphs separated by blank lines. "
        "Avoid unverifiable statistics, fabricated quotations, and unsupported claims."
    )
    user_prompt = (
        f"Video subject: {subject}\n"
        f"Script language: {language}\n"
        f"Number of paragraphs: {paragraph_count}\n"
        f"Additional guidance: {custom_prompt or 'None'}"
    )

    try:
        with OpenAI(**client_options) as client:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        content = completion.choices[0].message.content
        if not isinstance(content, str):
            raise AIGenerationError("AI returned no text. Please try again.")
        script, keywords = _parse_result(content)

    except AuthenticationError as exc:
        raise AIGenerationError("AI authentication failed. Check your API key.") from exc
    except RateLimitError as exc:
        raise AIGenerationError("AI provider rate limit or quota reached.") from exc
    except APITimeoutError as exc:
        raise AIGenerationError("AI request timed out. Please retry.") from exc
    except APIConnectionError as exc:
        raise AIGenerationError("Cannot connect to the AI provider.") from exc
    except OpenAIError as exc:
        # Do not pass upstream error contents, credentials, or request details to UI.
        raise AIGenerationError(
            "AI provider rejected the request. Check model, base URL, and account access."
        ) from exc

    return {
        "script": script,
        "keywords": keywords,
        "language_requested": language,
        "mode": "ai",
        "model": model,
    }
