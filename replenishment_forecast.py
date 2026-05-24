"""
Replenishment Forecast Agent — produces ranked reorder recommendations.

Public function: forecast_replenishment(sales_history, current_inventory,
                                        calendar_context, store_metadata) -> ReplenishmentForecastOutput
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from base import call_claude

from replenishment_prompt import REPLENISHMENT_SYSTEM_PROMPT

from schemas import ReplenishmentForecastOutput


def forecast_replenishment(
    sales_history: list[dict[str, Any]],
    current_inventory: dict[str, int],
    calendar_context: dict[str, Any],
    store_metadata: dict[str, Any],
) -> ReplenishmentForecastOutput:
    """Generate a replenishment forecast for the store."""

    user_message = json.dumps(
        {
            "sales_history": sales_history,
            "current_inventory": current_inventory,
            "calendar_context": calendar_context,
            "store_metadata": store_metadata,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    demo_response = _demo_forecast(
        sales_history, current_inventory, calendar_context, store_metadata
    )

    return call_claude(
        system_prompt=REPLENISHMENT_FORECAST_SYSTEM_PROMPT,
        user_message=user_message,
        output_schema=ReplenishmentForecastOutput,
        max_tokens=3000,
        demo_response=demo_response,
    )


def _demo_forecast(
    sales_history, current_inventory, calendar_context, store_metadata
) -> dict:
    """Deterministic demo forecast computed without LLM, for offline demos."""
    recs = []
    total_value = 0.0
    today = calendar_context.get("today", str(date.today()))

    upcoming_festivals = calendar_context.get("upcoming_festivals", [])
    nearest_festival = upcoming_festivals[0] if upcoming_festivals else None
    festival_within_window = (
        nearest_festival and nearest_festival.get("days_away", 999) <= 21
    )

    for item in sales_history:
        sku_id = item["sku_id"]
        last_30 = item.get("last_30d", [])
        if not last_30:
            continue
        # Weighted velocity: last 7 days half, prior 23 half
        last_7_avg = sum(last_30[-7:]) / 7
        prior_avg = sum(last_30[:-7]) / max(len(last_30[:-7]), 1)
        velocity = last_7_avg * 0.5 + prior_avg * 0.5

        stock = current_inventory.get(sku_id, 0)
        days_cover = stock / velocity if velocity > 0 else 999
        lead = item.get("supplier_lead_days", 3) + 2

        # Festival multiplier (simplified)
        festival_mult = 1.0
        festival_note = None
        if festival_within_window:
            name = nearest_festival["name"].lower()
            sku_lower = item["sku_name"].lower()
            if "diwali" in name:
                if "atta" in sku_lower or "wheat" in sku_lower:
                    festival_mult, festival_note = 1.4, "Diwali ×1.4 on atta"
                elif "oil" in sku_lower or "ghee" in sku_lower:
                    festival_mult, festival_note = 1.8, "Diwali ×1.8 on oil"
                elif "sugar" in sku_lower or "ghee" in sku_lower:
                    festival_mult, festival_note = 1.5, "Diwali ×1.5"
                else:
                    festival_mult, festival_note = 1.1, "Diwali ×1.1"
            elif "pongal" in name or "sankranti" in name:
                if "rice" in sku_lower or "jaggery" in sku_lower or "sugar" in sku_lower:
                    festival_mult, festival_note = 1.6, "Pongal ×1.6"

        # Reorder trigger
        if days_cover < lead * festival_mult:
            if days_cover < lead:
                priority = "CRITICAL"
            elif festival_within_window:
                priority = "HIGH"
            else:
                priority = "MEDIUM"

            order_qty = max(
                int(velocity * festival_mult * (lead + 7) - stock), 5
            )
            est_price = item.get("est_unit_price", 100)
            line_value = order_qty * est_price
            total_value += line_value

            recs.append(
                {
                    "sku_id": sku_id,
                    "sku_name": item["sku_name"],
                    "priority": priority,
                    "current_stock": stock,
                    "daily_velocity": round(velocity, 2),
                    "days_of_cover": round(days_cover, 2),
                    "recommended_order_qty": order_qty,
                    "recommended_supplier": item.get("supplier"),
                    "confidence": 0.85 if len(last_30) >= 30 else 0.6,
                    "reasoning": _build_reasoning(
                        item["sku_name"],
                        velocity,
                        days_cover,
                        order_qty,
                        festival_note,
                    ),
                    "festival_factor_applied": festival_note,
                }
            )

    # Sort by priority
    pri_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recs.sort(key=lambda r: pri_order[r["priority"]])

    summary = _build_summary(recs, nearest_festival)

    return {
        "forecast_date": today,
        "store_id": store_metadata.get("store_id", "UNKNOWN"),
        "recommendations": recs,
        "summary": summary,
        "data_gaps": [],
        "total_estimated_order_value_inr": round(total_value, 2),
    }


def _build_reasoning(name, velocity, days_cover, qty, festival_note):
    base = (
        f"{name} sells about {velocity:.1f} units/day. "
        f"Current stock will last {days_cover:.1f} days. "
    )
    if festival_note:
        base += f"{festival_note} bumps demand. "
    base += f"Recommend ordering {qty} units to cover the next ~10 days."
    return base


def _build_summary(recs, festival):
    if not recs:
        return "Stock comfortable. No urgent orders today."
    crit = [r for r in recs if r["priority"] == "CRITICAL"]
    high = [r for r in recs if r["priority"] == "HIGH"]
    parts = []
    if crit:
        names = ", ".join(r["sku_name"].split()[0] for r in crit[:3])
        parts.append(f"{len(crit)} items critical (run out soon): {names}.")
    if high and festival:
        parts.append(f"{festival['name']} in {festival['days_away']} days — order high-priority items today.")
    elif high:
        parts.append(f"{len(high)} high-priority items to reorder this week.")
    return " ".join(parts) if parts else "Review recommendations below."
