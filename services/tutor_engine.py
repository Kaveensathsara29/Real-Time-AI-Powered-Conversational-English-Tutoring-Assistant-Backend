import json
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from config import settings

SCENARIOS = {
    "casual": {
        "id": "casual",
        "title": "Casual Coffee Chat",
        "role": "Friendly English Native Friend (Alex)",
        "cefr_level": "A2 - B1",
        "difficulty": "Easy",
        "icon": "Coffee",
        "description": "Relaxed everyday conversation about hobbies, weekend plans, food, and culture.",
        "starters": [
            "Hey Alex! How has your week been going so far?",
            "I'm planning to learn how to cook Italian food this weekend.",
            "What's your favorite way to relax after a busy day?"
        ],
        "system_prompt": (
            "You are Alex, a warm, supportive, and friendly native English speaker having coffee with a learner. "
            "Speak naturally, use engaging everyday idioms, keep responses conversational (2-3 sentences), "
            "and always end with an open question to keep the user speaking."
        )
    },
    "job_interview": {
        "id": "job_interview",
        "title": "Tech Job Interview",
        "role": "Senior Hiring Manager (Eleanor)",
        "cefr_level": "B2 - C1",
        "difficulty": "Advanced",
        "icon": "Briefcase",
        "description": "Professional behavioral & technical interview practice with constructive feedback.",
        "starters": [
            "Good morning. Thank you for inviting me to interview today.",
            "I have 3 years of experience developing web applications.",
            "Could you tell me more about the challenges your engineering team faces?"
        ],
        "system_prompt": (
            "You are Eleanor, a polite yet incisive Senior Hiring Manager at an international tech company. "
            "Conduct a realistic English interview. Ask about their previous experience, leadership skills, "
            "and how they handle conflict. Keep your tone professional and encouraging."
        )
    },
    "ielts_speaking": {
        "id": "ielts_speaking",
        "title": "IELTS Speaking Examiner",
        "role": "Certified IELTS Examiner (Dr. Arthur)",
        "cefr_level": "B1 - C2",
        "difficulty": "Challenging",
        "icon": "GraduationCap",
        "description": "Simulated IELTS Part 1, 2, and 3 speaking test with band descriptor evaluations.",
        "starters": [
            "Good afternoon examiner, I'm ready to begin Part 1.",
            "In my hometown, public transportation has improved significantly over the past decade.",
            "I believe artificial intelligence will transform higher education in the next few years."
        ],
        "system_prompt": (
            "You are Dr. Arthur, an official British Council IELTS Speaking Examiner. "
            "Ask structured IELTS questions covering Lexical Resource, Fluency, and Grammatical Range. "
            "Keep the test formal, structured, and gently probe for deeper explanations."
        )
    },
    "restaurant": {
        "id": "restaurant",
        "title": "Gourmet Restaurant",
        "role": "Attentive Head Waiter (Marco)",
        "cefr_level": "A1 - B1",
        "difficulty": "Beginner",
        "icon": "Utensils",
        "description": "Ordering food, asking for recommendations, dealing with special dietary needs and the bill.",
        "starters": [
            "Hi, do you have a table for two available near the window?",
            "What would you recommend for someone who loves seafood?",
            "Could we please have the bill whenever you're ready?"
        ],
        "system_prompt": (
            "You are Marco, a polite and charming head waiter at a fine dining restaurant in London. "
            "Greet the guest warmly, explain menu options, clarify orders, and make polite recommendations."
        )
    },
    "debate": {
        "id": "debate",
        "title": "Philosophy & Debate Club",
        "role": "Oxford Debate Moderator (Julian)",
        "cefr_level": "B2 - C2",
        "difficulty": "Master",
        "icon": "Flame",
        "description": "Fast-paced intellectual sparring on technology, ethics, society, and climate change.",
        "starters": [
            "I argue that remote work is fundamentally healthier for society than office work.",
            "Should social media platforms be held legally accountable for user content?",
            "Can economic growth and climate sustainability truly coexist?"
        ],
        "system_prompt": (
            "You are Julian, an articulate debate champion. Challenge the user's arguments logically, "
            "offer counter-perspectives, use sophisticated rhetoric and transitional phrases, and encourage critical thinking."
        )
    },
    "travel_airport": {
        "id": "travel_airport",
        "title": "Airport & Border Customs",
        "role": "Immigration Officer (Officer Davis)",
        "cefr_level": "A2 - B2",
        "difficulty": "Practical",
        "icon": "Plane",
        "description": "Answering customs questions, flight check-ins, transit, and baggage claim situations.",
        "starters": [
            "Hello Officer, here is my passport and boarding pass.",
            "I am visiting for two weeks for a technology conference and sightseeing.",
            "Excuse me, where can I find the luggage claim for flight BA-182?"
        ],
        "system_prompt": (
            "You are Officer Davis at International Border Control. Ask routine immigration questions: "
            "purpose of visit, duration of stay, accommodation, and declarations in a calm, authoritative manner."
        )
    }
}

def _call_gemini_api_sync(key: str, payload: dict, requested_model: str) -> Optional[Dict[str, Any]]:
    """Synchronous HTTP worker for Gemini with automatic fallback models."""
    candidate_models = [requested_model]
    for fallback in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-3.8-flash"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)
            
    with httpx.Client(timeout=22.0) as client:
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    elif raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    raw_text = raw_text.strip()
                    parsed = json.loads(raw_text)
                    return parsed
                elif res.status_code in (404, 429, 503):
                    print(f"[Gemini API Warning] Model {model} returned {res.status_code}, trying next model...")
                    continue
                else:
                    print(f"[Gemini API Warning] Response {res.status_code}: {res.text}")
                    break
            except Exception as e:
                print(f"[Gemini API Exception with {model}] {e}")
                continue
    return None

async def generate_response_from_llm(
    prompt: str,
    history: List[Dict[str, str]],
    scenario_id: str,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Call Google Gemini API exclusively."""
    scenario = SCENARIOS.get(scenario_id, SCENARIOS["casual"])
    sys_instruction = scenario["system_prompt"]
    
    # Exclusively use Gemini API key (from request or environment)
    key = (api_key or settings.GEMINI_API_KEY).strip()
    if not key or key == "GEMINI_API_KEY":
        return None
        
    model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash") or "gemini-3.5-flash"
    
    contents = []
    for msg in history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    coaching_prompt = (
        f"{sys_instruction}\n\n"
        "CRITICAL COACHING RULES:\n"
        "You are an encouraging, expert English Speaking Coach and conversation partner.\n"
        "1. CAREFULLY INSPECT the user's latest message for ANY mistakes (grammar, verb tense, irregular past tense, prepositions, singular/plural, word order, or awkward phrasing).\n"
        "2. IF THE USER MADE ANY MISTAKE:\n"
        "   - 'grammar_feedback': Give a clear, helpful, and concise explanation of the exact mistake and the correct rule.\n"
        "   - 'reply': Gently correct the mistake right at the start of your spoken reply (e.g. \"Great effort! Just remember to say 'I bought' instead of 'I buyed'.\"), then smoothly answer their idea in your role and ask a friendly open question to keep them talking.\n"
        "3. IF NO MISTAKES WERE MADE:\n"
        "   - 'grammar_feedback': Leave as an empty string \"\".\n"
        "   - 'reply': Respond naturally and engagingly in your character's persona, ending with a question.\n"
        "4. 'native_alternative': Provide how a fluent native speaker would naturally say the same thought.\n"
        "5. 'cefr_level': Rate the learner's utterance (A1, A2, B1, B2, C1, or C2).\n"
        "6. 'pronunciation_focus_word': Provide one interesting or corrected word for pronunciation practice.\n\n"
        "You MUST respond ONLY in valid JSON matching this schema:\n"
        "{\n"
        "  \"reply\": \"(warm correction if mistake + conversational persona response + follow-up question)\",\n"
        "  \"grammar_feedback\": \"(specific error explanation or empty string)\",\n"
        "  \"native_alternative\": \"(natural native phrasing)\",\n"
        "  \"cefr_level\": \"(A1, A2, B1, B2, C1, or C2)\",\n"
        "  \"pronunciation_focus_word\": \"(focus word)\"\n"
        "}"
    )
    
    payload = {
        "system_instruction": {
            "parts": [{"text": coaching_prompt}]
        },
        "contents": contents,
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.7,
            "maxOutputTokens": 1000
        }
    }
    
    return await asyncio.to_thread(_call_gemini_api_sync, key, payload, model)

async def process_user_utterance(
    text: str,
    history: List[Dict[str, str]],
    scenario_id: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Exclusively processes user utterance through Google Gemini API."""
    llm_res = await generate_response_from_llm(text, history, scenario_id, api_key)
    if llm_res and "reply" in llm_res:
        return {
            "reply": llm_res.get("reply", ""),
            "grammar_feedback": llm_res.get("grammar_feedback", ""),
            "native_alternative": llm_res.get("native_alternative", ""),
            "cefr_level": llm_res.get("cefr_level", "B1"),
            "fluency_score": llm_res.get("fluency_score", 85),
            "vocab_tips": llm_res.get("vocab_tips", []),
            "pronunciation_focus_word": llm_res.get("pronunciation_focus_word", "articulation")
        }
        
    return {
        "reply": "I'm having trouble connecting to Google Gemini right now. Please verify your Gemini API key and internet connection.",
        "grammar_feedback": "",
        "native_alternative": "",
        "cefr_level": "N/A",
        "fluency_score": 0,
        "vocab_tips": [],
        "pronunciation_focus_word": ""
    }