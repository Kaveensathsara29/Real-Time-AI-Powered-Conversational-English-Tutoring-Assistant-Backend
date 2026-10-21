import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.tutor_engine import process_user_utterance
from services.tts_service import generate_speech_bytes

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/conversation")
async def conversation_websocket(websocket: WebSocket):
    await websocket.accept()
    session_history = []
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Real-time AI English Speaker WebSocket Connected"
        })
        
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type", "user_speech")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
                
            if msg_type == "user_speech":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue
                    
                scenario_id = data.get("scenario_id", "casual")
                voice = data.get("voice", "en-US-JennyNeural")
                api_key = data.get("api_key", None)
                
                # Acknowledge thinking state to animate AI red aura
                await websocket.send_json({"type": "ai_thinking", "status": "processing"})
                
                # Append to history
                session_history.append({"role": "user", "content": user_text})
                
                # Process with tutor engine
                result = await process_user_utterance(
                    text=user_text,
                    history=session_history,
                    scenario_id=scenario_id,
                    api_key=api_key
                )
                
                reply_text = result.get("reply", "")
                session_history.append({"role": "assistant", "content": reply_text})
                
                # Synthesize TTS audio
                audio_base64 = None
                try:
                    audio_bytes = await generate_speech_bytes(text=reply_text, voice=voice)
                    if audio_bytes:
                        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                except Exception as e:
                    print(f"WS TTS error: {e}")
                    
                # Dispatch comprehensive real-time payload
                await websocket.send_json({
                    "type": "ai_response",
                    "reply": reply_text,
                    "grammar_feedback": result.get("grammar_feedback", ""),
                    "native_alternative": result.get("native_alternative", ""),
                    "cefr_level": result.get("cefr_level", "B1"),
                    "fluency_score": result.get("fluency_score", 85),
                    "vocab_tips": result.get("vocab_tips", []),
                    "pronunciation_focus_word": result.get("pronunciation_focus_word", ""),
                    "audio_base64": audio_base64
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket session exception: {e}")
