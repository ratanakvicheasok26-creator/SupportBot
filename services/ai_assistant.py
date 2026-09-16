import os
import asyncio
import logging
from typing import List, Dict, Optional
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, KNOWLEDGE_BASE_PATH
from database import get_all_learned_corrections

logger = logging.getLogger(__name__)

# Cached client instance
_client_instance: Optional[genai.Client] = None

def get_genai_client() -> Optional[genai.Client]:
    """Returns a singleton client instance for fast inference."""
    global _client_instance
    if _client_instance is None and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        _client_instance = genai.Client(api_key=GEMINI_API_KEY)
    return _client_instance

def load_knowledge_base() -> str:
    """Load business knowledge base from file."""
    if os.path.exists(KNOWLEDGE_BASE_PATH):
        try:
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading knowledge_base.txt: {e}")
    return "You are a helpful system information specialist for the Camera Surveillance & AI Platform."

async def generate_ai_response(
    customer_name: str,
    message_text: str,
    recent_history: List[Dict[str, str]] = None
) -> Optional[str]:
    """
    Generates a fast, intelligent, and technically accurate response using Gemini AI,
    explaining the Camera Surveillance platform architecture, features, and workflows.
    """
    client = get_genai_client()
    if not client:
        return None

    knowledge_base = load_knowledge_base()
    
    # Retrieve learned corrections from past mistakes/admin feedback
    learned_items = await get_all_learned_corrections()
    learned_text = ""
    if learned_items:
        learned_lines = [f"- [ID: {item['id']}] {item['guidance']}" for item in learned_items]
        learned_text = "\n=== LEARNED TECHNICAL RULES & CORRECTIONS ===\n" + "\n".join(learned_lines) + "\n============================================\n"

    system_instruction = f"""
You are the official Technical System Information Specialist for the AI Camera Surveillance & Operations Platform.
User Name: {customer_name}

=== SYSTEM KNOWLEDGE BASE ===
{knowledge_base}
=============================
{learned_text}
CORE INSTRUCTIONS & GUIDELINES:
1. **System & Workflow Focus (No Sales/Pricing)**:
   - Your primary role is to clearly explain how the camera surveillance system works, the end-to-end workflow (Video Ingestion -> Edge AI Inference -> Spatial Zone Rule Engine -> Telegram Alerts/Dashboard), camera compatibility (RTSP, ONVIF, Hikvision, Dahua, Uniview, Tapo, Webcams), local edge architecture, and AI vision capabilities.
   - Do NOT push sales pitches, promotional offers, booking pitches, or pricing unless the user explicitly asks about technical specs or general facts. Keep responses focused on system information, technical explanations, and workflows.
2. **Linguistic Fluency & Tone**:
   - Understand standard Khmer script, English, and romanized Khmer phrases.
   - Respond in the exact language the user uses (polite, natural Khmer with "បាទ/ចាស, ជម្រាបសួរ, សូមអរគុណ, លោកអ្នក" or clean professional English).
   - Format answers clearly with bullet points and bold highlights for readability.
3. **Strict Technical Grounding**:
   - Strictly adhere to the knowledge base facts (Local Edge computing, 100% data privacy, RTSP/ONVIF streams, Telegram real-time alerts with snapshots, sub-second latency).
   - Do not hallucinate non-existent features.
4. **Learned Rules Priority**:
   - If a rule or correction appears in the 'LEARNED TECHNICAL RULES & CORRECTIONS' section above, prioritize that instruction.
"""

    # Format conversation history
    contents = []
    if recent_history:
        for item in recent_history:
            role = "user" if item.get("sender_type") == "customer" else "model"
            text = item.get("text_content", "").strip()
            if text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text)]
                    )
                )

    # Append current customer message
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message_text)]
        )
    )

    models_to_try = [
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.6-flash",
        "gemini-flash-latest"
    ]

    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.5,
                    max_output_tokens=1000
                )
            )

            if response and response.text:
                return response.text.strip()

        except Exception as e:
            logger.warning(f"Model {model_name} error: {e}. Trying fallback...")
            await asyncio.sleep(0.1)

    return None
