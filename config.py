import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Real-Time AI English Speaker"
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Gemini LLM configuration (Only Google Gemini is supported)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    
    # Default TTS voice
    DEFAULT_VOICE: str = os.getenv("DEFAULT_VOICE", "en-US-JennyNeural")
    DEFAULT_RATE: str = os.getenv("DEFAULT_RATE", "+0%")
    DEFAULT_PITCH: str = os.getenv("DEFAULT_PITCH", "+0Hz")

settings = Settings()
