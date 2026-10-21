import edge_tts
import io
from typing import List, Dict

AVAILABLE_VOICES: List[Dict[str, str]] = [
    {"id": "en-US-JennyNeural", "name": "Jenny (US - Warm & Natural)", "gender": "Female", "accent": "American"},
    {"id": "en-US-GuyNeural", "name": "Guy (US - Confident & Friendly)", "gender": "Male", "accent": "American"},
    {"id": "en-US-AriaNeural", "name": "Aria (US - Expressive & Lively)", "gender": "Female", "accent": "American"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (UK - Elegant & Clear)", "gender": "Female", "accent": "British"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK - Professional & Calm)", "gender": "Male", "accent": "British"},
    {"id": "en-AU-NatashaNeural", "name": "Natasha (AU - Friendly & Bright)", "gender": "Female", "accent": "Australian"},
    {"id": "en-CA-ClaraNeural", "name": "Clara (CA - Gentle & Articulate)", "gender": "Female", "accent": "Canadian"},
    {"id": "en-IN-NeerjaNeural", "name": "Neerja (IN - Crisp & Helpful)", "gender": "Female", "accent": "Indian"}
]

async def generate_speech_bytes(text: str, voice: str = "en-US-JennyNeural", rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """Generate MP3 audio bytes using edge-tts."""
    cleaned_text = text.strip()
    if not cleaned_text:
        return b""
    
    communicate = edge_tts.Communicate(cleaned_text, voice=voice, rate=rate, pitch=pitch)
    audio_buffer = io.BytesIO()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
            
    return audio_buffer.getvalue()
