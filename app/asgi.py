from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import re
from app.controllers.v1.video_tasks import router as video_tasks_router
from app.controllers.v1.ai_scripts import router as ai_scripts_router

app = FastAPI(
    title="Macy AI API",
    description="AI-Powered Video Generation Backend",
    version="1.0.0",
)

app.include_router(ai_scripts_router)
app.include_router(video_tasks_router)


class ScriptPreviewRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=300)
    language: str = "Auto Detect"
    paragraph_count: int = Field(default=3, ge=1, le=12)

@app.get("/")
def home():
    return {
        "message": "Welcome to Macy AI API",
        "version": "1.0.0",
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Macy AI Backend",
    }

@app.post("/api/v1/scripts/demo")
def generate_demo_script(request: ScriptPreviewRequest):
    topic = request.subject.strip()

    if len(topic) < 3:
        raise HTTPException(
            status_code=422,
            detail="Subject must contain at least 3 characters.",
        )

    templates = [
        f"Today, we're exploring {topic}.",
        f"Let's understand why {topic} is important.",
        f"We'll discover some interesting ideas and practical examples related to {topic}.",
        f"There are many ways this subject connects to our everyday lives.",
        f"Thanks for watching this introduction to {topic}.",
    ]

    paragraphs = [
        templates[i % len(templates)]
        for i in range(request.paragraph_count)
    ]

    script = "\n\n".join(paragraphs)

    stop_words = {
        "the", "and", "for", "with", "how",
        "why", "what", "are", "this", "that",
        "from", "into", "about", "you", "your",
    }

    words = re.findall(r"[a-zA-Z]{3,}", topic.lower())

    keywords = list(
        dict.fromkeys(
            word for word in words
            if word not in stop_words
        )
    )[:8]

    if not keywords:
        keywords = [topic]

    return {
        "script": script,
        "keywords": keywords,
        "language_requested": request.language,
        "mode": "demo",
    }