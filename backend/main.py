from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from .models import engine, Base, SessionLocal, Driver  # this triggers the DB creation
from google_auth_oauthlib.flow import InstalledAppFlow


# ── Load environment variables from .env file ────────────────────────────────
load_dotenv()

# Create OpenAI client using the key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple in-memory storage for chat context (per driver)
# Key = driver_id (int), Value = dict with language and original text
# chat_memory = {}  # Example: {1: {"language": "en", "original_text": "I need a taxi"}}
# Simple memory: remembers customer's language per driver
# Key = driver_id (int), Value = customer's language code (e.g. "fr")
driver_language_memory = {}

# ── Create the FastAPI application ───────────────────────────────────────────
app = FastAPI(
    title="TaxiTranslator API",
    description="Helps customers and Greek taxi drivers communicate across languages",
    version="0.1.0"
)


# ── Data models ────────────────────────────────────────────────────────────────

class CustomerMessage(BaseModel):
    driver_id: int                  # Required — links message to driver
    text: str
    source_language: Optional[str] = None # optional – OpenAI can detect it


class TranslatedResponse(BaseModel):
    original_text: str
    translated_to_greek: str
    detected_language: str                  # now always filled by OpenAI


class DriverMessage(BaseModel):
    driver_id: int                  # Required — same driver
    text: str
    customer_language: Optional[str] = None  # Optional now — try to remember it

class DriverTranslatedResponse(BaseModel):
    original_greek: str
    translated_to_customer: str
    customer_language: str

class DriverRegister(BaseModel):
    whatsapp_number: str
    email: str


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
    Saves detected language to memory for future replies
    """
    if not msg.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    try:
        prompt = f"""
        1. Detect the language of the following message.
        2. Translate it to natural, polite, everyday Greek (suitable for a taxi driver).
        
        Rules:
        - Return ONLY a valid JSON object — nothing else.
        - Use standard ISO 639-1 language codes: "en", "fr", "de", "es", "it", "ru", etc.
        - If detection is uncertain → use "unknown"
        - Greek translation should be friendly and clear.

        Message: {msg.text}

        Example output:
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
            temperature=0.15,
            max_tokens=250
        )

        raw_content = response.choices[0].message.content.strip()

        try:
            result = json.loads(raw_content)
            detected_lang = result.get("detected_language", "unknown")
            greek_text = result.get("translated_to_greek", "[Translation failed]")
        except json.JSONDecodeError:
            detected_lang = "unknown"
            greek_text = raw_content

        # Save detected language to memory for this driver
        driver_language_memory[msg.driver_id] = detected_lang

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
    Driver (Greek) → back to customer's original language
    Automatically uses remembered language from previous customer message
    """
    if not msg.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    # Load remembered language for this driver
    remembered_lang = driver_language_memory.get(msg.driver_id)

    # Use remembered language if available, otherwise require it
    customer_language = remembered_lang or msg.customer_language

    if not customer_language:
        raise HTTPException(
            status_code=400,
            detail="customer_language required (or send a customer message first with driver_id to detect it)"
        )

    try:
        prompt = f"""
        Translate the following Greek message to natural, polite {customer_language}.
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
            customer_language=customer_language
        )

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            raise HTTPException(status_code=500, detail="OpenAI API key issue — check .env")
        raise HTTPException(status_code=500, detail=f"Translation failed: {error_msg}")
        

@app.post("/register-driver")
async def register_driver(driver: DriverRegister):
    """
    Register a new driver with their WhatsApp number and email.
    This will allow us to store their calendar token later.
    """
    if not driver.whatsapp_number.strip() or not driver.email.strip():
        raise HTTPException(status_code=400, detail="Both whatsapp_number and email are required")

    db = SessionLocal()
    try:
        # Check for existing driver
        existing = db.query(Driver).filter(Driver.whatsapp_number == driver.whatsapp_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="This WhatsApp number is already registered")

        # Create and save new driver
        new_driver = Driver(
            whatsapp_number=driver.whatsapp_number,
            email=driver.email,
            calendar_token=""  # empty until linked
        )

        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)  # get the auto-generated ID

        return {
            "message": "Driver registered successfully",
            "driver_id": new_driver.id,
            "whatsapp_number": new_driver.whatsapp_number,
            "email": new_driver.email
        }

    except HTTPException as http_exc:
        db.rollback()
        raise http_exc

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    finally:
        db.close()    
    
@app.get("/drivers")
async def list_drivers():
    """
    List all registered drivers (for testing/debugging).
    Returns their ID, WhatsApp number, and email.
    """
    db = SessionLocal()
    try:
        drivers = db.query(Driver).all()
        return [
            {
                "id": driver.id,
                "whatsapp_number": driver.whatsapp_number,
                "email": driver.email,
                "has_calendar_linked": bool(driver.calendar_token)  # True if token is not empty
            }
            for driver in drivers
        ]
    finally:
        db.close()

@app.get("/link-calendar/{driver_id}")
async def link_calendar(driver_id: int):
    db = SessionLocal()
    try:
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        # 1. Setup the flow
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json',
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )

        # 2. Explicitly tell the local server to use port 8080
        # The library will try to open http://localhost:8080/
        creds = flow.run_local_server(
            port=8080, 
            prompt='consent',
            authorization_prompt_message=''
        ) 

        # 3. Save token
        driver.calendar_token = creds.to_json()
        db.commit()
        
        return {"message": f"Success! Calendar linked for driver {driver_id}."}
        
    except Exception as e:
        # It's helpful to see the full error in your console during dev
        print(f"Error occurred: {e}")
        return {"error": str(e)}
    finally:
        db.close()



# This endpoint is for testing the WhatsApp simulation without needing the actual WhatsApp integration.

class WhatsAppSimulation(BaseModel):
    from_number: str          # driver's WhatsApp number
    text: str                 # customer's message
    is_reply: bool = False    # True if this is driver's reply

@app.post("/simulate-whatsapp")
async def simulate_whatsapp(msg: WhatsAppSimulation):
    """
    Simulate a WhatsApp message coming from a customer to a driver.
    Finds the driver by WhatsApp number and translates accordingly.
    """
    db = SessionLocal()
    try:
        # Find the driver by their WhatsApp number
        driver = db.query(Driver).filter(Driver.whatsapp_number == msg.from_number).first()
        if not driver:
            raise HTTPException(status_code=404, detail="No driver registered with this WhatsApp number")

        if not msg.is_reply:
            # Customer → Greek (normal message)
            translation = await translate_customer_message(CustomerMessage(text=msg.text))
            return {
                "driver_id": driver.id,
                "driver_whatsapp": driver.whatsapp_number,
                "original_customer_text": msg.text,
                "translated_to_greek": translation.translated_to_greek,
                "detected_language": translation.detected_language,
                "next_step": "Copy the translated_to_greek and send to customer chat in WhatsApp"
            }
        else:
            # Driver reply (Greek → customer's language)
            # For now we require customer_language — later we can remember it
            customer_language = "en"  # ← hard-coded for test; improve later
            reply_translation = await translate_driver_reply(
                DriverMessage(text=msg.text, customer_language=customer_language)
            )
            return {
                "driver_id": driver.id,
                "original_greek_reply": msg.text,
                "translated_to_customer": reply_translation.translated_to_customer,
                "customer_language_used": customer_language,
                "next_step": "Copy translated_to_customer and send back to customer in WhatsApp"
            }

    finally:
        db.close()