"""LLM factory for the agent layer.

Uses Google Gemini Flash via LangChain (free tier). The client is created
lazily and cached, and `llm_available()` lets callers degrade gracefully to a
deterministic heuristic engine when no API key is configured — so the whole
platform still runs and demos offline.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from app.config import settings


@lru_cache
def get_llm():
    """Return a cached LangChain chat model, or None if unavailable.

    Returns None when GOOGLE_API_KEY is missing or the SDK can't initialise,
    so callers can fall back to the heuristic evaluator.
    """
    if not settings.google_api_key:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=0,  # deterministic compliance judgments
        )
    except Exception:  # noqa: BLE001 — any import/config error -> heuristic mode
        return None


def llm_available() -> bool:
    return get_llm() is not None


def invoke_json(prompt: str) -> Optional[str]:
    """Invoke the LLM and return raw text, or None if the LLM is unavailable."""
    llm = get_llm()
    if llm is None:
        return None
    try:
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception:  # noqa: BLE001 — network/quota errors -> heuristic fallback
        return None
