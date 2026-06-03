# config/ai_provider.py
"""
AI Provider Factory — supports Groq (free), Gemini (free), Anthropic (paid), Ollama (local).
Switch providers by changing AI_PROVIDER in your .env file.
"""
import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from langfuse import Langfuse, observe, get_client

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

# Initialize Langfuse client gracefully
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

langfuse_client = None
if LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY:
    try:
        langfuse_client = Langfuse(
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY,
            host=LANGFUSE_HOST
        )
    except Exception as e:
        print(f"Observability Warning: Langfuse failed to initialize: {e}")


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


@observe(as_type="generation", capture_input=False, capture_output=False)
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    reraise=True
)
def call_ai(system_prompt: str, user_message: str, max_tokens: int = 1024) -> dict:
    """
    Universal AI call that works with Groq, Anthropic, Gemini, or Ollama.
    Returns a dict: {"content": response_text, "tokens": total_tokens_used}
    Includes automatic retry with exponential backoff for rate limits.
    Traces metadata to Langfuse in a privacy-first manner.
    """
    client = get_ai_client()

    # Determine the model name for tracing
    if AI_PROVIDER == "groq":
        model_name = GROQ_MODEL
    elif AI_PROVIDER == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3")
    elif AI_PROVIDER == "anthropic":
        model_name = "claude-sonnet-4-5"
    elif AI_PROVIDER == "gemini":
        model_name = "gemini-1.5-flash"
    else:
        model_name = "unknown"

    # Start Langfuse trace/generation gracefully
    try:
        get_client().update_current_generation(
            name="call_ai",
            model=model_name,
            input={
                "system_prompt": system_prompt,
                "user_message": "<redacted>"
            },
            metadata={
                "provider": AI_PROVIDER,
            }
        )
    except Exception:
        pass

    content = ""
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    try:
        if AI_PROVIDER in ["groq", "ollama"]:
            response = client.chat.completions.create(
                model=model_name,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
            )
            content = response.choices[0].message.content
            if hasattr(response, "usage") and response.usage:
                prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
                completion_tokens = getattr(response.usage, "completion_tokens", 0)
                total_tokens = getattr(response.usage, "total_tokens", 0)

        elif AI_PROVIDER == "anthropic":
            response = client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            content = response.content[0].text
            if hasattr(response, "usage") and response.usage:
                prompt_tokens = getattr(response.usage, "input_tokens", 0)
                completion_tokens = getattr(response.usage, "output_tokens", 0)
                total_tokens = prompt_tokens + completion_tokens

        elif AI_PROVIDER == "gemini":
            model = client.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(user_message)
            content = response.text
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
                completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
                total_tokens = getattr(response.usage_metadata, "total_token_count", 0)
        else:
            raise ValueError(f"Provider {AI_PROVIDER} not implemented")

        # Update Langfuse on success
        try:
            get_client().update_current_generation(
                output={"content": "<redacted>"},
                usage_details={
                    "input": prompt_tokens,
                    "output": completion_tokens,
                    "total": total_tokens
                }
            )
        except Exception:
            pass

        return {"content": content, "tokens": total_tokens}

    except Exception as e:
        # Update Langfuse on failure
        try:
            get_client().update_current_generation(
                level="ERROR",
                status_message=str(e)
            )
        except Exception:
            pass
        raise e



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
