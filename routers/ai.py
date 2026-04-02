import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Load API Key from environment
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

class AIChatRequest(BaseModel):
    message: str

import requests as py_requests

@router.post("/chat")
async def chat_with_ai(request: AIChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"response": "Backend Error: Gemini API Key missing in .env file"}
        
    try:
        # Re-configure each time in case env changed, though normally top-level is fine
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-flash-latest')
        
        response = model.generate_content(request.message)
        
        if response and response.text:
            return {"response": response.text}
        else:
            return {"response": "I'm sorry, I couldn't generate a response. Please try again."}
            
    except Exception as e:
        print(f"Chat Error: {str(e)}")
        # Check for specific API key errors
        if "API_KEY_INVALID" in str(e):
            return {"response": "Backend Error: Your Gemini API Key is invalid. Please check your .env file."}
        return {"response": f"AI Error: {str(e)}"}
