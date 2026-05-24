"""
Supplier PO Agent — drafts complete purchase orders from a verbal request.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from base import call_claude
from supplier_po_prompt import SUPPLIER_PO_SYSTEM_PROMPT
from schemas import SupplierPOOutput


def draft_purchase_order(
    request_context: dict[str, Any],
    supplier_catalog: dict[str, Any],
    replenishment_recommendations: list[dict[str, Any]],
    store_profile: dict[str, Any],
    recent_pos: list[dict[str, Any]] | None = None,
) -> SupplierPOOutput:
    """Draft a complete purchase order."""

    user_message = json.dumps(
        {
            "request_context": request_context,
            "supplier_catalog": supplier_catalog,
            "replenishment_recommendations": replenishment_recommendations,
            "recent_pos": recent_pos or [],
            "store_profile": store_profile,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    demo_response = _demo_po(
        request_context, supplier_catalog, replenishment_recommendations, store_profile
    )

    return call_claude(
        system_prompt=SUPPLIER_PO_SYSTEM_PROMPT,
        user_message=user_message,
        output_schema=SupplierPOOutput,
        max_tokens=2500,
        demo_response=demo_response,
    )


def _demo_po(request_context, supplier_catalog, recs, store_profile):
    """Deterministic demo PO."""
    today = date.today()
    expected_delivery = today + timedelta(days=supplier_catalog.get("lead_time_days", 4))

    supplier_sku_ids = {s["sku_id"] for s in supplier_catalog.get("skus", [])}
    matching_recs = [r for r in recs if r["sku_id"] in supplier_sku_ids and r["priority"] in ("CRITICAL", "HIGH", "MEDIUM")]
    matching_recs.sort(key=lambda r: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(r["priority"], 3))

    sku_price_map = {s["sku_id"]: s for s in supplier_catalog.get("skus", [])}

    line_items = []
    subtotal = 0.0
    for r in matching_recs[:8]:  # cap at 8 lines for demo
        sku_info = sku_price_map[r["sku_id"]]
        price = sku_info["last_price"]
        qty = r["recommended_order_qty"]
        line_total = price * qty
        subtotal += line_total
        line_items.append(
            {
                "sku_id": r["sku_id"],
                "sku_name": r["sku_name"],
                "quantity": qty,
                "unit": "packet",
                "last_known_price": price,
                "price_confirmation_needed": False,
                "estimated_line_total": round(line_total, 2),
                "source": "replenishment_forecast",
                "moq_validated": True,
            }
        )

    gst = round(subtotal * 0.05, 2)
    grand = round(subtotal + gst, 2)
    ceiling = store_profile.get("po_ceiling_inr", 50000)
    approval_needed = grand > ceiling

    po_num = f"{store_profile.get('code', 'STR')}-PO-{today.strftime('%y%m%d')}-{abs(hash(supplier_catalog.get('supplier_id', 'X'))) % 10000:04d}"

    summary_items = ", ".join(f"{l['sku_name'].split()[0]} {l['quantity']}" for l in line_items[:3])
    owner_summary = (
        f"{supplier_catalog['name']} ko order taiyar — {summary_items}"
        + (" aur baaki" if len(line_items) > 3 else "")
        + f". Total ₹{grand:.0f}. Delivery {expected_delivery.strftime('%d %b')} tak. Bhej dun?"
    )

    items_text = "\n".join(
        f"{i+1}. {l['sku_name']} — {l['quantity']} {l['unit']}s @ ₹{l['last_known_price']}"
        for i, l in enumerate(line_items)
    )
    supplier_msg = (
        f"Namaste, {store_profile['name']} ki taraf se order:\n{items_text}\n"
        f"Approximate value: ₹{grand:.0f} including GST. "
        f"Expected delivery: {expected_delivery.strftime('%d %b %Y')}. "
        f"Kripya confirm karein. — {store_profile['name']}"
    )

    return {
        "po_number": po_num,
        "po_date": str(today),
        "supplier": {
            "supplier_id": supplier_catalog["supplier_id"],
            "name": supplier_catalog["name"],
            "contact_phone": supplier_catalog["contact_phone"],
            "expected_delivery_date": str(expected_delivery),
        },
        "line_items": line_items,
        "totals": {
            "estimated_subtotal": round(subtotal, 2),
            "estimated_gst": gst,
            "estimated_grand_total": grand,
        },
        "requires_owner_approval": approval_needed,
        "approval_reason": f"PO ₹{grand:.0f} exceeds ₹{ceiling:.0f} ceiling" if approval_needed else None,
        "clarification_needed": False,
        "clarification_question": None,
        "owner_facing_summary": owner_summary,
        "supplier_facing_message": supplier_msg,
        "notes_to_owner": ["Prices reflect last known supplier rates."]
        + (["⚠️ Approval needed — over ceiling."] if approval_needed else []),
    }
