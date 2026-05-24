"""
Invoice Agent — generates GST-compliant invoices from parsed sale data.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from base import call_claude
from invoice_prompt import INVOICE_AGENT_SYSTEM_PROMPT
from schemas import InvoiceOutput


def generate_invoice(
    sale_data: dict[str, Any],
    sku_catalog: dict[str, Any],
    store_profile: dict[str, Any],
    customer_profile: dict[str, Any] | None = None,
    invoice_metadata: dict[str, Any] | None = None,
) -> InvoiceOutput:
    """Generate a GST-compliant invoice JSON."""

    if invoice_metadata is None:
        now = datetime.now()
        invoice_metadata = {
            "invoice_number": f"{store_profile.get('code', 'STR')}-{now.strftime('%y%m%d')}-{now.strftime('%H%M%S')}",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }

    if customer_profile is None:
        customer_profile = {
            "name": "Walk-in Customer",
            "phone": None,
            "gstin": None,
            "state_code": store_profile.get("state_code"),
        }

    user_message = json.dumps(
        {
            "sale_data": sale_data,
            "sku_catalog": sku_catalog,
            "store_profile": store_profile,
            "customer_profile": customer_profile,
            "invoice_metadata": invoice_metadata,
        },
        ensure_ascii=False,
        indent=2,
    )

    demo_response = _demo_invoice(
        sale_data, sku_catalog, store_profile, customer_profile, invoice_metadata
    )

    return call_claude(
        system_prompt=INVOICE_AGENT_SYSTEM_PROMPT,
        user_message=user_message,
        output_schema=InvoiceOutput,
        max_tokens=2500,
        demo_response=demo_response,
    )


def _demo_invoice(sale_data, sku_catalog, store_profile, customer_profile, meta):
    """Compute invoice deterministically without LLM."""
    line_items = []
    subtotal = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0

    same_state = (
        customer_profile.get("state_code") is None
        or customer_profile["state_code"] == store_profile["state_code"]
    )

    for item in sale_data.get("items", []):
        sku_id = item["matched_sku_id"]
        sku = sku_catalog.get(sku_id)
        if not sku:
            continue
        qty = item["quantity"]
        mrp = sku["mrp"]
        gst_rate = sku["gst_rate"]

        # MRP is inclusive of GST in India; back-calculate taxable value
        line_total = mrp * qty
        taxable = round(line_total / (1 + gst_rate / 100), 2)
        gst_amount = round(line_total - taxable, 2)

        cgst = round(gst_amount / 2, 2) if same_state else 0.0
        sgst = round(gst_amount / 2, 2) if same_state else 0.0
        igst = gst_amount if not same_state else 0.0

        line_items.append(
            {
                "sku_id": sku_id,
                "sku_name": sku["name"],
                "hsn_code": sku["hsn"],
                "quantity": qty,
                "unit_price": round(taxable / qty, 2),
                "discount_pct": 0.0,
                "taxable_value": taxable,
                "gst_rate": gst_rate,
                "cgst_amount": cgst,
                "sgst_amount": sgst,
                "igst_amount": igst,
                "line_total": round(line_total, 2),
            }
        )
        subtotal += taxable
        total_cgst += cgst
        total_sgst += sgst
        total_igst += igst

    grand_total = round(subtotal + total_cgst + total_sgst + total_igst, 2)
    round_off = round(round(grand_total) - grand_total, 2)
    grand_total_rounded = round(grand_total + round_off, 2)

    return {
        "invoice_number": meta["invoice_number"],
        "invoice_date": meta.get("invoice_date") or meta.get("date"),
        "invoice_time": meta.get("invoice_time") or meta.get("time"),
        "store": {
            "name": store_profile["name"],
            "gstin": store_profile["gstin"],
            "address": store_profile["address"],
            "state_code": store_profile["state_code"],
        },
        "customer": {
            "name": customer_profile.get("name", "Walk-in Customer"),
            "phone": customer_profile.get("phone"),
            "gstin": customer_profile.get("gstin"),
            "state_code": customer_profile.get("state_code"),
            "is_b2b": bool(customer_profile.get("gstin")),
        },
        "line_items": line_items,
        "totals": {
            "subtotal_taxable": round(subtotal, 2),
            "total_cgst": round(total_cgst, 2),
            "total_sgst": round(total_sgst, 2),
            "total_igst": round(total_igst, 2),
            "round_off": round_off,
            "grand_total": grand_total_rounded,
            "amount_in_words": _amount_in_words(grand_total_rounded),
        },
        "payment_mode": sale_data.get("payment_mode") or "cash",
        "irn_required": grand_total_rounded > 50000,
        "validation_errors": [],
        "owner_facing_summary": (
            f"{customer_profile.get('name', 'Customer')} ka bill ₹{grand_total_rounded:.0f} ka ban gaya. "
            f"{len(line_items)} items, {sale_data.get('payment_mode', 'cash')} mein."
        ),
    }


def _amount_in_words(amount: float) -> str:
    """Convert amount to Indian-format words."""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = [
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen",
        "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen",
    ]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def two_digits(n):
        if n < 10:
            return units[n]
        if n < 20:
            return teens[n - 10]
        return tens[n // 10] + (" " + units[n % 10] if n % 10 else "")

    def three_digits(n):
        if n >= 100:
            return units[n // 100] + " Hundred" + (" " + two_digits(n % 100) if n % 100 else "")
        return two_digits(n)

    rupees = int(amount)
    paise = round((amount - rupees) * 100)

    crore = rupees // 10000000
    rupees %= 10000000
    lakh = rupees // 100000
    rupees %= 100000
    thousand = rupees // 1000
    rupees %= 1000

    parts = []
    if crore:
        parts.append(two_digits(crore) + " Crore")
    if lakh:
        parts.append(two_digits(lakh) + " Lakh")
    if thousand:
        parts.append(two_digits(thousand) + " Thousand")
    if rupees:
        parts.append(three_digits(rupees))

    words = "Rupees " + " ".join(parts) if parts else "Rupees Zero"
    if paise:
        words += f" and {two_digits(paise)} Paise"
    words += " Only"
    return words
