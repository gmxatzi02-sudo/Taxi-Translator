from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

# ── Load environment variables from .env file ────────────────────────────────
load_dotenv()

# Create OpenAI client using the key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Create the FastAPI application ───────────────────────────────────────────
app = FastAPI(
    title="TaxiTranslator API",
    description="Helps customers and Greek taxi drivers communicate across languages",
    version="0.1.0"
)


# ── Data models ────────────────────────────────────────────────────────────────

class CustomerMessage(BaseModel):
    text: str
    source_language: Optional[str] = None   # optional – OpenAI can detect it


class TranslatedResponse(BaseModel):
    original_text: str
    translated_to_greek: str
    detected_language: Optional[str] = None


class DriverMessage(BaseModel):
    text: str                      # Greek message from the driver
    customer_language: str         # e.g. "en", "fr", "de" – required


class DriverTranslatedResponse(BaseModel):
    original_greek: str
    translated_to_customer: str
    customer_language: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Simple health check endpoint"""
    return {
        "message": "TaxiTranslator backend is running! 🚕",
        "status": "healthy",
        "docs": "/docs"
    }


@app.post("/translate", response_model=TranslatedResponse)
async def translate_customer_message(msg: CustomerMessage):
    """
    Customer (any language) → Greek
    Automatically detects language and translates to polite Greek
    """
    if not msg.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    try:
        prompt = f"""
        1. Detect the language of the following message.
        2. Translate it to natural, polite, everyday Greek (suitable for a taxi driver).
        
        Rules:
        - Return ONLY a valid JSON object — nothing else.
        - Use standard language codes: "en", "fr", "de", "es", "it", "ru", etc.
        - If detection is uncertain → use "unknown"
        - Greek translation should be friendly and clear.

        Message: {msg.text}

        Example output (return exactly this format):
        {{
          "detected_language": "en",
          "translated_to_greek": "Γεια σου, χρειάζομαι ταξί στο αεροδρόμιο."
        }}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise translator and language detector. Respond only with valid JSON."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.2,
            max_tokens=200
        )

        raw_content = response.choices[0].message.content.strip()

        # Try to parse OpenAI's response as JSON
        try:
            result = json.loads(raw_content)
            detected_lang = result.get("detected_language", "unknown")
            greek_text = result.get("translated_to_greek", "[Translation failed]")
        except json.JSONDecodeError:
            # Fallback if OpenAI didn't return clean JSON
            detected_lang = "unknown"
            greek_text = raw_content

        return TranslatedResponse(
            original_text=msg.text,
            translated_to_greek=greek_text,
            detected_language=detected_lang
        )

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
            raise HTTPException(status_code=500, detail="OpenAI API key missing or invalid. Check .env file.")
        raise HTTPException(status_code=500, detail=f"Translation failed: {error_msg}")


@app.post("/translate-driver", response_model=DriverTranslatedResponse)
async def translate_driver_reply(msg: DriverMessage):
    """
    Driver (Greek) → Customer original language
    Needs to know the customer's language to translate back correctly
    """
    if not msg.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    if not msg.customer_language:
        raise HTTPException(status_code=400, detail="customer_language is required (e.g. 'en', 'fr')")

    try:
        prompt = f"""
        Translate the following Greek message to natural, polite {msg.customer_language}.
        Use everyday language suitable for a taxi customer.
        Return ONLY a valid JSON object — nothing else.

        Greek message: {msg.text}

        Example output:
        {{
          "translated_to_customer": "Hello, I'll be there in 5 minutes.",
          "original_greek": "Ελληνικό μήνυμα εδώ"
        }}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise translator. Respond only with valid JSON."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )

        raw_content = response.choices[0].message.content.strip()

        try:
            result = json.loads(raw_content)
            translated_text = result.get("translated_to_customer", "[Translation failed]")
            original_greek = result.get("original_greek", msg.text)
        except json.JSONDecodeError:
            translated_text = raw_content
            original_greek = msg.text

        return DriverTranslatedResponse(
            original_greek=original_greek,
            translated_to_customer=translated_text,
            customer_language=msg.customer_language
        )

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            raise HTTPException(status_code=500, detail="OpenAI API key issue — check .env")
        raise HTTPException(status_code=500, detail=f"Translation failed: {error_msg}")