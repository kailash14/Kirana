"""
Voice Parser Agent — converts raw voice transcripts to structured action JSON.

Public function: parse_voice_command(transcript, store_context) -> VoiceParseOutput
"""

from __future__ import annotations

import json
from typing import Any

from agents.base import call_claude
from prompts.voice_parser_prompt import VOICE_PARSER_SYSTEM_PROMPT
from schemas import VoiceParseOutput


def parse_voice_command(
    transcript: str, store_context: dict[str, Any]
) -> VoiceParseOutput:
    """
    Args:
        transcript: raw voice transcript (may be code-mixed Tamil/Hindi/English)
        store_context: dict with at least:
            - sku_catalog: list of {sku_id, name, aliases}
            - recent_sales: list of recent sale records (for anaphora resolution)
            - active_customer_ref: optional, last named customer

    Returns:
        VoiceParseOutput
    """
    user_message = json.dumps(
        {
            "transcript": transcript,
            "sku_catalog": store_context.get("sku_catalog", []),
            "recent_sales": store_context.get("recent_sales", []),
            "active_customer_ref": store_context.get("active_customer_ref"),
        },
        ensure_ascii=False,
        indent=2,
    )

    demo_response = _demo_response_for(transcript, store_context)

    return call_claude(
        system_prompt=VOICE_PARSER_SYSTEM_PROMPT,
        user_message=user_message,
        output_schema=VoiceParseOutput,
        demo_response=demo_response,
    )


def _demo_response_for(transcript: str, store_context: dict) -> dict:
    """Heuristic demo response when no API key is set — for local demos."""
    lower = transcript.lower()
    catalog = store_context.get("sku_catalog", [])

    # Find any SKU whose alias or name appears in the transcript
    matched_sku = None
    for sku in catalog:
        for alias in [sku["name"].lower()] + [a.lower() for a in sku.get("aliases", [])]:
            if alias in lower:
                matched_sku = sku
                break
        if matched_sku:
            break

    # Heuristic quantity extraction
    qty = 1
    for num_str, num_val in {
        "ek ": 1, "one ": 1, "do ": 2, "two ": 2, "rendu ": 2,
        "teen ": 3, "three ": 3, "moonu ": 3,
        "char ": 4, "four ": 4, "naalu ": 4,
        "paanch ": 5, "five ": 5, "anju ": 5,
    }.items():
        if num_str in lower:
            qty = num_val
            break
    # Also look for digit numbers
    import re
    digit_match = re.search(r"\b(\d+)\b", transcript)
    if digit_match:
        qty = int(digit_match.group(1))

    # Stem-based matching so Hindi/Tamil verb variants are tolerated in demo mode.
    # The real LLM path handles morphology natively; these stems are only the offline fallback.
    has_festival = any(w in lower for w in ["diwali", "pongal", "festival", "eid", "ramzan", "christmas", "navratri", "rakhi", "ratha yatra"])
    has_question = any(w in lower for w in ["kya", "kaisa", "kitna", "chahiye", "should i", "what should", "kaun"])
    has_time_horizon = any(w in lower for w in ["next week", "agle hafte", "agle mahine", "next month", "kal", "tomorrow"])

    if any(w in lower for w in ["kitna stock", "stock kitna", "kitne", "stock hai", "evvalavu", "how many", "how much"]):
        intent = "CHECK_STOCK"
    elif any(w in lower for w in ["bill", "invoice", "rasid", "rasidh", "receipt"]):
        intent = "GENERATE_INVOICE"
    # Forecast/advisory: festival + question OR explicit forecast phrasing — must precede DRAFT_PO
    elif (has_festival and has_question) or has_time_horizon or "forecast" in lower:
        intent = "FORECAST_QUERY"
    elif any(w in lower for w in ["order kar", "order de", "supplier", "patanjali", "itc", "metro", "bharat grains", "annapurna"]):
        intent = "DRAFT_PO"
    # Sale verbs across Hindi/Tamil/English — match on stems
    elif any(stem in lower for stem in ["sold", "bech", "bik", "kuduth", "kuduthen", "kudu", "diya", "diye", "becha", "bichka"]):
        intent = "LOG_SALE"
    elif any(stem in lower for stem in ["aaya", "aayi", "aagaya", "delivery", "received", "receive", "stock aa", "milgaya"]):
        intent = "LOG_RECEIPT"
    elif has_festival:
        intent = "FORECAST_QUERY"
    else:
        intent = "UNCLEAR"

    payment = None
    if "cash" in lower or "nagad" in lower:
        payment = "cash"
    elif "upi" in lower or "phonepe" in lower or "gpay" in lower:
        payment = "upi"
    elif "udhar" in lower or "credit" in lower:
        payment = "credit"

    customer_ref = None
    for marker in ["uncle", "aunty", "sir", "madam"]:
        if marker in lower:
            words = transcript.split()
            for i, w in enumerate(words):
                if marker in w.lower() and i > 0:
                    customer_ref = f"{words[i-1]} {w}"
                    break
            break

    items = []
    if matched_sku and intent in ("LOG_SALE", "LOG_RECEIPT", "GENERATE_INVOICE"):
        items.append({
            "colloquial_name": matched_sku["name"].split()[0],
            "matched_sku_id": matched_sku["sku_id"],
            "matched_sku_name": matched_sku["name"],
            "match_confidence": 0.92,
            "quantity": qty,
            "unit": "packet",
        })
    elif intent == "CHECK_STOCK" and matched_sku:
        items.append({
            "colloquial_name": matched_sku["name"].split()[0],
            "matched_sku_id": None,
            "matched_sku_name": None,
            "match_confidence": 0.0,
            "quantity": 0,
            "unit": None,
        })

    return {
        "intent": intent,
        "confidence": 0.85 if intent != "UNCLEAR" else 0.3,
        "items": items,
        "customer_reference": customer_ref,
        "supplier_reference": "Patanjali" if "patanjali" in lower else None,
        "payment_mode": payment,
        "clarification_needed": intent == "UNCLEAR",
        "clarification_question": (
            "Kya karna hai? Thoda detail mein bataiye." if intent == "UNCLEAR" else None
        ),
        "raw_language_detected": "mixed",
        "reasoning": "Demo-mode heuristic parse.",
    }
