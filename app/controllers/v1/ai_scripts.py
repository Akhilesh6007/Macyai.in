"""Live AI script endpoint. Keep the existing /demo route in app/asgi.py."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.llm import (
    AIConfigurationError,
    AIGenerationError,
    generate_ai_script,
)

router = APIRouter(prefix="/api/v1/scripts", tags=["AI Script Generation"])


class GenerateScriptRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=300)
    language: str = Field(default="Auto Detect", max_length=40)
    paragraph_count: int = Field(default=3, ge=1, le=12)
    custom_prompt: str = Field(default="", max_length=1500)


@router.post("/generate")
def generate_script(request: GenerateScriptRequest):
    try:
        return generate_ai_script(
            subject=request.subject.strip(),
            language=request.language,
            paragraph_count=request.paragraph_count,
            custom_prompt=request.custom_prompt,
        )
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AIGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
