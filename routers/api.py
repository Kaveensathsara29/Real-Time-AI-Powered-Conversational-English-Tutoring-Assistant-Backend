import base64
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel
from typing import List, Optional
from services.tutor_engine import SCENARIOS, process_user_utterance
from services.tts_service import AVAILABLE_VOICES, generate_speech_bytes

router = APIRouter(prefix="/api", tags=["API"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    scenario_id: str = "casual"
    history: List[ChatMessage] = []
    api_key: Optional[str] = None
    voice: Optional[str] = "en-US-JennyNeural"
    return_audio: bool = True

@router.get("/scenarios")
async def get_scenarios():
    """Return all interactive practice scenarios."""
    return list(SCENARIOS.values())

@router.get("/voices")
async def get_voices():
    """Return available TTS voices."""
    return AVAILABLE_VOICES

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Process a user utterance, generate AI reply, feedback, and synthesized voice."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]
    
    tutor_result = await process_user_utterance(
        text=req.message,
        history=history_dicts,
        scenario_id=req.scenario_id,
        api_key=req.api_key
    )
    
    audio_base64 = None
    if req.return_audio and tutor_result.get("reply"):
        try:
            audio_bytes = await generate_speech_bytes(
                text=tutor_result["reply"],
                voice=req.voice or "en-US-JennyNeural"
            )
            if audio_bytes:
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            print(f"TTS generation error: {e}")
            
    return {
        **tutor_result,
        "audio_base64": audio_base64
    }

@router.get("/tts")
async def stream_tts(
    text: str = Query(..., description="Text to synthesize"),
    voice: str = Query("en-US-JennyNeural", description="Voice ID"),
    rate: str = Query("+0%", description="Speech rate adjustment"),
    pitch: str = Query("+0Hz", description="Speech pitch adjustment")
):
    """Streaming TTS audio endpoint returning audio/mpeg."""
    try:
        audio_bytes = await generate_speech_bytes(text=text, voice=voice, rate=rate, pitch=pitch)
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Failed to synthesize audio")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
