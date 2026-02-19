from google import genai


client = genai.Client(
    api_key="AIzaSyCluHRykXYKQdDYzEvdfu90wZBkwQrWtSk"
)

MODEL_NAME = "models/gemini-flash-latest"

# ===============================
# SYSTEM PROMPTS (TWO MODES)
# ===============================

STRICT_BOOKFLIX_PROMPT = """
You are BookFlix AI, an in-app book recommendation assistant.

ABSOLUTE RULES:
- You MUST talk ONLY about the books explicitly provided
- You MUST NOT invent, suggest, or mention any other books
- You MUST NOT greet the user
- You MUST NOT recommend books from your general knowledge
- You MUST NOT write essays or reviews
- Keep responses short, clear, and practical
- Speak like a bookstore helper inside an app

Tone:
- Calm
- Friendly
- Direct
- No therapy language
"""

CHAT_PROMPT = """
You are BookFlix AI, a friendly in-app assistant.

Rules:
- Sound natural and human
- Keep responses short
- Do NOT act like a therapist
- Do NOT invent books unless asked for recommendations
"""

# ===============================
# LLM CALL
# ===============================
def ask_llm(message: str, mode: str = "chat") -> str:
    system_prompt = (
        STRICT_BOOKFLIX_PROMPT
        if mode == "strict"
        else CHAT_PROMPT
    )

    full_prompt = f"""
{system_prompt}

USER MESSAGE:
{message}

INSTRUCTIONS:
- Plain text only
- Follow rules strictly
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt
        )

        parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text"):
                parts.append(part.text)

        return "".join(parts).strip()

    except Exception:
        return "I’m having trouble right now. Please try again."
