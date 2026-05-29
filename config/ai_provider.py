# config/ai_provider.py
"""
AI Provider Factory — supports Groq (free), Gemini (free), Anthropic (paid), Ollama (local).
Switch providers by changing AI_PROVIDER in your .env file.
"""
import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

# ── Fix: Groq 0.9.0 passes `proxies` to httpx which dropped it in 0.28+ ──────
try:
    import httpx as _httpx
    _orig_init = _httpx.Client.__init__
    def _patched_init(self, *args, **kwargs):
        kwargs.pop("proxies", None)
        _orig_init(self, *args, **kwargs)
    _httpx.Client.__init__ = _patched_init

    _orig_async_init = _httpx.AsyncClient.__init__
    def _patched_async_init(self, *args, **kwargs):
        kwargs.pop("proxies", None)
        _orig_async_init(self, *args, **kwargs)
    _httpx.AsyncClient.__init__ = _patched_async_init
except Exception:
    pass

from groq import Groq

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")


def get_ai_client():
    """Return the configured AI client."""
    if AI_PROVIDER == "groq":
        return Groq(api_key=os.getenv("GROQ_API_KEY"))
    elif AI_PROVIDER == "anthropic":
        import anthropic
        return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    elif AI_PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        return genai
    elif AI_PROVIDER == "ollama":
        # Ollama uses OpenAI-compatible API — no key needed
        from openai import OpenAI
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {AI_PROVIDER}")


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    reraise=True
)
def call_ai(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """
    Universal AI call that works with Groq, Anthropic, Gemini, or Ollama.
    Returns the text response as a string.
    Includes automatic retry with exponential backoff for rate limits.
    """
    client = get_ai_client()

    if AI_PROVIDER in ["groq", "ollama"]:
        model = GROQ_MODEL if AI_PROVIDER == "groq" else os.getenv("OLLAMA_MODEL", "llama3")
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,  # Low temperature for consistent classification
        )
        return response.choices[0].message.content

    elif AI_PROVIDER == "anthropic":
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    elif AI_PROVIDER == "gemini":
        model = client.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )
        response = model.generate_content(user_message)
        return response.text

    raise ValueError(f"Provider {AI_PROVIDER} not implemented")


def parse_json_response(raw_text: str) -> dict:
    """
    Safely parse JSON from AI response.
    Handles cases where the model wraps JSON in markdown code blocks.
    """
    text = raw_text.strip()

    # Strip markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "Failed to parse AI response", "raw": text}
