import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
# from dotenv import load_dotenv

# # 1. Load environment variables
# load_dotenv()

# 2. Configure Gemini (Cleaned up)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("CRITICAL: GEMINI_API_KEY is missing from your .env file!")
else:
    genai.configure(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Efficiency: Load HTML once
try:
    with open("main.html", "r", encoding="utf-8") as f:
        HTML_CONTENT = f.read()
except FileNotFoundError:
    HTML_CONTENT = "<html><body><h1>main.html not found</h1></body></html>"

class ChatRequest(BaseModel):
    message: str
    system_prompt: str = ""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    # Securely inject the Maps key
    maps_key = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_KEY_MISSING")
    return HTML_CONTENT.replace("MAP_key", maps_key)

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # AS OF APRIL 2026: 
        # 'gemini-2.5-flash' is the most stable free-tier model (10 RPM).
        # 'gemini-3-flash-preview' is also available but has tighter limits.
        model_instance = genai.GenerativeModel('gemini-2.5-flash')
        
        # We send the system prompt and message together
        full_prompt = f"{request.system_prompt}\n\nUser: {request.message}"
        response = model_instance.generate_content(full_prompt)
        
        return {"response": response.text}
        
    except Exception as e:
        # If you still see 'limit: 0', your API key is likely tied to a 
        # legacy project. See the 'Fresh Start' tip below.
        print(f"--- API ERROR ---")
        print(e) 
        raise HTTPException(status_code=500, detail="The AI is currently resetting. Please try again.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)