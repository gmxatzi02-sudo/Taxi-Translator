from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="TaxiTranslator")

class CustomerMessage(BaseModel):
    text: str
    source_language: Optional[str] = None   # optional, we'll auto-detect later


class TranslatedResponse(BaseModel):
    original_text: str
    translated_to_greek: str
    # Later we'll also add: translated_back_to_customer, original_greek_reply, etc.

@app.get("/")
def root():
    return {"message": "TaxiTranslator backend is alive! 🚕"}

@app.post("/translate", response_model=TranslatedResponse)
async def translate_customer_message(msg: CustomerMessage):
    # Fake translation logic (we replace this with OpenAI later)
    fake_greek = f"[FAKE-GR] {msg.text} → γεια σου φίλε ταξιτζή"

    return TranslatedResponse(
        original_text=msg.text,
        translated_to_greek=fake_greek
    )