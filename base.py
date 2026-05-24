"""
Base Anthropic API client wrapper for DukaanAI agents.

Encapsulates:
  - API key handling (env var ANTHROPIC_API_KEY)
  - Demo mode (returns canned responses if no key, so the Streamlit app runs anywhere)
  - JSON extraction + Pydantic validation
  - Retry logic on malformed JSON
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Model identifier — uses Claude Sonnet 4.5 by default; can be overridden
DEFAULT_MODEL = os.getenv("DUKAAN_MODEL", "claude-sonnet-4-5")
DEFAULT_MAX_TOKENS = 2048

# Demo-mode toggle: if no API key, the app still runs with canned responses
DEMO_MODE = os.getenv("ANTHROPIC_API_KEY") is None

T = TypeVar("T", bound=BaseModel)


def _strip_json_fences(text: str) -> str:
    """Strip ```json ... ``` fences if the model wrapped its output."""
    text = text.strip()
    if text.startswith("```"):
        # Drop opening fence (with optional language tag)
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        # Drop closing fence
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def call_claude(
    system_prompt: str,
    user_message: str,
    output_schema: Type[T],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.2,
    demo_response: dict | None = None,
) -> T:
    """
    Call Claude with a system prompt + user message; parse output into the given Pydantic schema.

    Raises ValidationError if the model output cannot be coerced into the schema after one retry.
    """

    if DEMO_MODE:
        if demo_response is None:
            raise RuntimeError(
                "DEMO_MODE is on (no ANTHROPIC_API_KEY set) and no demo_response was provided."
            )
        return output_schema.model_validate(demo_response)

    # Lazy import so the file imports cleanly even without the SDK installed
    from anthropic import Anthropic

    client = Anthropic()

    def _invoke(retry_hint: str | None = None) -> str:
        messages = [{"role": "user", "content": user_message}]
        if retry_hint:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous output failed JSON validation. "
                        f"Issue: {retry_hint}. "
                        "Return ONLY valid JSON matching the schema, no other text."
                    ),
                }
            )

        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages,
        )

        # Concatenate text blocks
        text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        return "".join(text_parts)

    raw = _invoke()
    cleaned = _strip_json_fences(raw)

    try:
        payload = json.loads(cleaned)
        return output_schema.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning("First-pass JSON validation failed: %s. Retrying with hint.", e)
        raw_retry = _invoke(retry_hint=str(e))
        cleaned_retry = _strip_json_fences(raw_retry)
        payload_retry = json.loads(cleaned_retry)
        return output_schema.model_validate(payload_retry)
