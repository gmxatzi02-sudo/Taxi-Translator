from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load secrets from .env file (very important!)
load_dotenv()

# Create OpenAI client — it reads the key from .env automatically
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(
    title="TaxiTranslator API",
    description="Helps customers and Greek taxi drivers communicate across languages",
    version="0.1.0"
)


# ── Data models ────────────────────────────────────────────────────────────────

class CustomerMessage(BaseModel):
    text: str
    source_language: Optional[str] = None   # optional — OpenAI can detect it


class TranslatedResponse(BaseModel):
    original_text: str
    translated_to_greek: str
    detected_language: Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "TaxiTranslator backend is running! 🚕",
        "status": "healthy",
        "docs": "/docs"
    }


@app.post("/translate", response_model=TranslatedResponse)
async def translate_customer_message(msg: CustomerMessage):
    """
    Translates customer's message (any language) → Greek using OpenAI
    Returns both original and translated text
    """
    if not msg.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    try:
        # Prepare a clear prompt for OpenAI
        prompt = f"""
        Translate the following customer message to natural, polite, everyday Greek.
        Use language suitable for a taxi driver.
        Return **only** the Greek translation — no explanations, no quotes, nothing else.

        Message: {msg.text}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",           # cheap, fast and very good at translation
            messages=[
                {"role": "system", "content": "You are a helpful, accurate translator."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.2,               # low = more consistent / accurate
            max_tokens=150
        )

        # Get the translated text
        greek_text = response.choices[0].message.content.strip()

        # Very basic language detection (we'll improve later)
        detected = msg.source_language or "auto-detected"

        return TranslatedResponse(
            original_text=msg.text,
            translated_to_greek=greek_text,
            detected_language=detected
        )

    except Exception as e:
        # Show a friendly error instead of crashing
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
            raise HTTPException(status_code=500, detail="OpenAI API key is missing or invalid. Check .env file.")
        raise HTTPException(status_code=500, detail=f"Translation failed: {error_msg}")