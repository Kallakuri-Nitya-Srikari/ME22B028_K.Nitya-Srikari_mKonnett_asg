"""Simple OpenAI LLM wrapper to produce natural language outputs.
The agent computes numeric answers locally and uses the LLM to produce a polished reply.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None

def polish_response(summary_text: str, user_query: str, max_tokens: int = 300) -> str:
    """Call the LLM to turn a short structured summary into a natural-language answer.
    If OpenAI is not installed or API key is missing, return the summary_text with a header.
    """
    if not OPENAI_API_KEY or openai is None:
        return f"(no OPENAI) {summary_text}"

    prompt = [
        {"role": "system", "content": "You are a helpful sales assistant. Keep answers concise and user-friendly."},
        {"role": "user", "content": f"User query: {user_query}\n\nData summary:\n{summary_text}\n\nProduce a concise answer (2-6 sentences) and a short bulleted list if appropriate."}
    ]

    try:
        # Use ChatCompletion for compatibility. If unavailable, fallback to Completion.
        resp = openai.ChatCompletion.create(model=OPENAI_MODEL, messages=prompt, max_tokens=max_tokens, temperature=0.1)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"(LLM failed: {e})\n{summary_text}"
