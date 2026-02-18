from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Example of a message route
@app.post("/messages/")
async def create_message(message: str):
    return {"message": message}

# Example of a translation route
@app.post("/translate/")
async def translate(text: str, target_language: str):
    return {"translated_text": f"{text} in {target_language}"}

# Example of a booking route
@app.post("/book/")
async def create_booking(details: dict):
    return {"booking_details": details}