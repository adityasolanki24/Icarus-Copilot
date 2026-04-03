"""
Configuration for the v2 mission planning system.

Set these environment variables (or in .env):
    LLM_PROVIDER: google | openai | anthropic  (default: google)
    LLM_MODEL:    model name override           (default: per-provider)
    GOOGLE_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
"""

import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")
LLM_MODEL = os.getenv("LLM_MODEL", "")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

DEFAULT_MODELS = {
    "google": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
}

_API_KEY_MAP = {
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def get_model() -> str:
    return LLM_MODEL or DEFAULT_MODELS.get(LLM_PROVIDER, "gpt-4o-mini")


def get_api_key() -> str:
    keys = {
        "google": GOOGLE_API_KEY,
        "openai": OPENAI_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
    }
    key = keys.get(LLM_PROVIDER)
    if not key:
        env_var = _API_KEY_MAP.get(LLM_PROVIDER, "???")
        raise ValueError(
            f"API key not found for provider '{LLM_PROVIDER}'. "
            f"Set {env_var} in your .env file."
        )
    return key
