"""
DukaanAI — Streamlit chat interface.

Run with:
    streamlit run app.py

The app works in two modes:
  1. DEMO MODE (no API key) — deterministic responses from heuristic logic
  2. LIVE MODE (with ANTHROPIC_API_KEY env var) — calls Claude for real

Why two modes: lets reviewers / interviewers run the demo without provisioning an API key.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Make repo importable
sys.path.insert(0, str(Path(__file__).parent))

from voice_parser import parse_voice_command
from replenishment_forecast import forecast_replenishment
from invoice_agent import generate_invoice
from supplier_po_agent import draft_purchase_order
from base import DEMO_MODE

from seed_data import (
    SKU_CATALOG,
    SUPPLIERS,
    CURRENT_INVENTORY,
    SALES_HISTORY,
    STORE_PROFILE,
    DEMO_SUGGESTIONS,
    get_calendar_context,
)

st.set_page_config(
    page_title="DukaanAI — Voice-First Retail Assistant",
    page_icon="🏪",
    layout="wide",
)


# ============================================================
# Session state
# ============================================================

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    f"Namaste! Main DukaanAI hun — aapka store assistant. "
                    f"Aaj {get_calendar_context()['day_of_week']}, "
                    f"{get_calendar_context()['today']}. Kuch poochiye ya bataiye."
                ),
            }
        ]
    if "inventory" not in st.session_state:
        st.session_state.inventory = dict(CURRENT_INVENTORY)
    if "sales_log" not in st.session_state:
        st.session_state.sales_log = []
    if "invoice_counter" not in st.session_state:
        st.session_state.invoice_counter = 142
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None
    if "last_customer" not in st.session_state:
        st.session_state.last_customer = None


init_state()


# ============================================================
# Helpers
# ============================================================

def sku_by_id(sku_id):
    return next((s for s in SKU_CATALOG if s["sku_id"] == sku_id), None)


def supplier_by_name_match(name_fragment):
    if not name_fragment:
        return None
    frag = name_fragment.lower()
    for s in SUPPLIERS:
        if frag in s["name"].lower():
            return s
    return None


def supplier_catalog_for(supplier):
    """Build the supplier_catalog payload for the PO agent."""
    return {
        "supplier_id": supplier["supplier_id"],
        "name": supplier["name"],
        "contact_phone": supplier["contact_phone"],
        "lead_time_days": supplier["lead_time_days"],
        "moq_default": supplier["moq_default"],
        "skus": [
            {
                "sku_id": sku["sku_id"],
                "name": sku["name"],
                "last_price": round(sku["mrp"] * 0.92, 2),
                "last_priced_on": "2026-05-15",
            }
            for sku in SKU_CATALOG
            if sku["sku_id"] in supplier["sku_ids_carried"]
        ],
    }


def process_owner_command(transcript: str) -> str:
    """Top-level orchestrator (Python; the Conversational Router prompt is for the LLM version).

    For the demo, we orchestrate in code to keep latency low and to make the flow visible.
    In production, the Conversational Router prompt would do this routing inside the LLM.
    """
    # Step 1: Parse
    store_context = {
        "sku_catalog": [
            {"sku_id": s["sku_id"], "name": s["name"], "aliases": s.get("aliases", [])}
            for s in SKU_CATALOG
        ],
        "recent_sales": st.session_state.sales_log[-5:],
        "active_customer_ref": st.session_state.last_customer,
    }

    parse = parse_voice_command(transcript, store_context)

    # Show the parse in an expander for transparency (great for demos)
    with st.expander("🔍 Voice Parser output (transparency)", expanded=False):
        st.json(parse.model_dump())

    # Step 2: Route based on intent
    if parse.clarification_needed:
        return f"❓ {parse.clarification_question}"

    intent = parse.intent

    if intent == "LOG_SALE":
        return _handle_log_sale(parse)
    if intent == "LOG_RECEIPT":
        return _handle_log_receipt(parse)
    if intent == "CHECK_STOCK":
        return _handle_stock_check(parse)
    if intent == "GENERATE_INVOICE":
        return _handle_invoice(parse)
    if intent == "DRAFT_PO":
        return _handle_draft_po(parse)
    if intent == "FORECAST_QUERY":
        return _handle_forecast()
    if intent == "ADJUST_STOCK":
        return _handle_adjust_stock(parse)
    return "Samajh nahi aaya. Thoda detail mein boliye?"


def _handle_log_sale(parse):
    lines = []
    sale_total = 0.0
    sale_items_logged = []
    for item in parse.items:
        if not item.matched_sku_id:
            continue
        sku = sku_by_id(item.matched_sku_id)
        if not sku:
            continue
        qty = int(item.quantity)
        current_stock = st.session_state.inventory.get(item.matched_sku_id, 0)
        if qty > current_stock:
            lines.append(
                f"⚠️ {sku['name']} sirf {current_stock} stock mein, par {qty} sale ka log ho raha hai. "
                f"Pakka {qty} bika tha?"
            )
        # Deduct
        st.session_state.inventory[item.matched_sku_id] = max(0, current_stock - qty)
        line_value = sku["mrp"] * qty
        sale_total += line_value
        sale_items_logged.append({"sku": sku["name"], "qty": qty, "value": line_value})

    if parse.customer_reference:
        st.session_state.last_customer = parse.customer_reference

    st.session_state.sales_log.append(
        {
            "timestamp": datetime.now().isoformat(),
            "items": [it.model_dump() for it in parse.items],
            "customer": parse.customer_reference,
            "payment_mode": (parse.payment_mode if isinstance(parse.payment_mode, str)
                             else (parse.payment_mode.value if parse.payment_mode else "cash")),
            "total": sale_total,
        }
    )

    items_str = ", ".join(f"{i['qty']} × {i['sku'].split()[0]}" for i in sale_items_logged)
    customer_str = f" {parse.customer_reference} ko" if parse.customer_reference else ""
    payment_str = ""
    if parse.payment_mode:
        pmode = parse.payment_mode if isinstance(parse.payment_mode, str) else parse.payment_mode.value
        payment_str = f" ({pmode})"

    response = f"✅ Sale log ho gaya{customer_str}: {items_str} — ₹{sale_total:.0f}{payment_str}."
    if lines:
        response += "\n\n" + "\n".join(lines)
    response += "\n\nBill chahiye?"
    return response


def _handle_log_receipt(parse):
    lines = []
    for item in parse.items:
        if not item.matched_sku_id:
            continue
        sku = sku_by_id(item.matched_sku_id)
        qty = int(item.quantity)
        st.session_state.inventory[item.matched_sku_id] = (
            st.session_state.inventory.get(item.matched_sku_id, 0) + qty
        )
        lines.append(f"{sku['name']}: +{qty} (ab total {st.session_state.inventory[item.matched_sku_id]})")
    return "📦 Stock receipt logged:\n" + "\n".join(lines) if lines else "Kya receive hua?"


def _handle_stock_check(parse):
    # If a colloquial name was given, find all SKUs matching that name fragment
    if not parse.items:
        return "Kis cheez ka stock check karna hai?"
    colloq = parse.items[0].colloquial_name.lower()
    matches = []
    for sku in SKU_CATALOG:
        if colloq in sku["name"].lower() or any(colloq in a.lower() for a in sku.get("aliases", [])):
            stock = st.session_state.inventory.get(sku["sku_id"], 0)
            matches.append(f"• {sku['name']}: **{stock}** units")
    if not matches:
        return f"'{colloq}' nahi mila stock mein. Spelling check karein?"
    return "📊 Stock status:\n" + "\n".join(matches)


def _handle_invoice(parse):
    # Use most recent sale unless overridden
    if not st.session_state.sales_log:
        return "Pichla sale nahi mila. Pehle sale log karein."
    last_sale = st.session_state.sales_log[-1]

    sale_data = {
        "items": last_sale["items"],
        "customer_reference": last_sale.get("customer"),
        "payment_mode": last_sale["payment_mode"],
    }
    sku_catalog_dict = {
        s["sku_id"]: {
            "name": s["name"], "hsn": s["hsn"], "gst_rate": s["gst_rate"], "mrp": s["mrp"]
        }
        for s in SKU_CATALOG
    }

    st.session_state.invoice_counter += 1
    invoice_meta = {
        "invoice_number": f"SLS-{datetime.now().strftime('%y%m%d')}-{st.session_state.invoice_counter:04d}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
    }
    customer_profile = {
        "name": last_sale.get("customer") or "Walk-in Customer",
        "phone": None,
        "gstin": None,
        "state_code": STORE_PROFILE["state_code"],
    }

    invoice = generate_invoice(
        sale_data,
        sku_catalog_dict,
        STORE_PROFILE,
        customer_profile,
        invoice_meta,
    )

    # Render invoice
    inv_md = _render_invoice_markdown(invoice)
    with st.expander("🧾 Generated invoice", expanded=True):
        st.markdown(inv_md)
        st.download_button(
            "Download Invoice (text)",
            inv_md,
            file_name=f"{invoice.invoice_number}.txt",
            key=f"inv_{invoice.invoice_number}",
        )

    return f"✅ {invoice.owner_facing_summary}"


def _render_invoice_markdown(inv):
    lines_md = "\n".join(
        f"| {l.sku_name} | {l.hsn_code} | {l.quantity} | ₹{l.unit_price:.2f} | ₹{l.taxable_value:.2f} | {l.gst_rate}% | ₹{l.line_total:.2f} |"
        for l in inv.line_items
    )
    return f"""
**TAX INVOICE — {inv.invoice_number}**
**Date:** {inv.invoice_date} {inv.invoice_time}

**Seller:** {inv.store.name}
GSTIN: {inv.store.gstin}
{inv.store.address}

**Buyer:** {inv.customer.name}

| Item | HSN | Qty | Unit ₹ | Taxable | GST | Total |
|---|---|---|---|---|---|---|
{lines_md}

|  |  |
|---|---|
| Subtotal (Taxable) | ₹{inv.totals.subtotal_taxable:.2f} |
| CGST | ₹{inv.totals.total_cgst:.2f} |
| SGST | ₹{inv.totals.total_sgst:.2f} |
| IGST | ₹{inv.totals.total_igst:.2f} |
| Round Off | ₹{inv.totals.round_off:.2f} |
| **Grand Total** | **₹{inv.totals.grand_total:.2f}** |

**Amount in words:** {inv.totals.amount_in_words}
**Payment Mode:** {inv.payment_mode}
"""


def _handle_draft_po(parse):
    supplier = supplier_by_name_match(parse.supplier_reference)
    if not supplier:
        return "Konsa supplier? Patanjali, Metro, Bharat Grains, Annapurna, ya Local Dairy?"

    # Run forecast first to populate recommendations
    calendar_ctx = get_calendar_context()
    forecast = forecast_replenishment(
        SALES_HISTORY,
        st.session_state.inventory,
        calendar_ctx,
        STORE_PROFILE,
    )
    recs_dict = [r.model_dump() for r in forecast.recommendations]

    po = draft_purchase_order(
        request_context={
            "supplier_reference": supplier["name"],
            "items": [],
            "reasoning": "Open-ended order request",
        },
        supplier_catalog=supplier_catalog_for(supplier),
        replenishment_recommendations=recs_dict,
        store_profile=STORE_PROFILE,
    )

    # Render
    po_md = _render_po_markdown(po)
    with st.expander("📋 Drafted Purchase Order", expanded=True):
        st.markdown(po_md)
        st.code(po.supplier_facing_message, language="text")

    return f"📋 {po.owner_facing_summary}"


def _render_po_markdown(po):
    items_md = "\n".join(
        f"| {l.sku_name} | {l.quantity} | ₹{l.last_known_price:.2f} | ₹{l.estimated_line_total:.2f} |"
        for l in po.line_items
    )
    notes_md = "\n".join(f"- {n}" for n in po.notes_to_owner)
    return f"""
**PURCHASE ORDER — {po.po_number}**
**Date:** {po.po_date}
**Supplier:** {po.supplier.name}
**Expected Delivery:** {po.supplier.expected_delivery_date}

| Item | Qty | Rate | Line Total |
|---|---|---|---|
{items_md}

| | |
|---|---|
| Subtotal | ₹{po.totals.estimated_subtotal:.2f} |
| GST (est.) | ₹{po.totals.estimated_gst:.2f} |
| **Grand Total (est.)** | **₹{po.totals.estimated_grand_total:.2f}** |

**Notes:**
{notes_md}
"""


def _handle_forecast():
    calendar_ctx = get_calendar_context()
    forecast = forecast_replenishment(
        SALES_HISTORY,
        st.session_state.inventory,
        calendar_ctx,
        STORE_PROFILE,
    )
    with st.expander("📈 Full forecast detail", expanded=True):
        for r in forecast.recommendations[:10]:
            badge = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}.get(
                r.priority if isinstance(r.priority, str) else r.priority.value, "⚪"
            )
            st.markdown(
                f"{badge} **{r.sku_name}** — order **{r.recommended_order_qty}** "
                f"(stock {r.current_stock}, ~{r.days_of_cover:.1f} days cover)\n\n"
                f"_{r.reasoning}_"
            )
    festival_str = ""
    if calendar_ctx["upcoming_festivals"]:
        nf = calendar_ctx["upcoming_festivals"][0]
        festival_str = f" {nf['name']} {nf['days_away']} din mein hai."
    return (
        f"📈 {forecast.summary}{festival_str} "
        f"Estimated order value: ₹{forecast.total_estimated_order_value_inr:.0f}."
    )


def _handle_adjust_stock(parse):
    notes = []
    for item in parse.items:
        if not item.matched_sku_id:
            continue
        qty = int(item.quantity)
        cur = st.session_state.inventory.get(item.matched_sku_id, 0)
        new_val = max(0, cur - qty)
        st.session_state.inventory[item.matched_sku_id] = new_val
        sku = sku_by_id(item.matched_sku_id)
        notes.append(f"{sku['name']}: -{qty} (now {new_val})")
    return "📉 Stock adjusted:\n" + "\n".join(notes)


# ============================================================
# UI
# ============================================================

# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🏪 DukaanAI")
    st.caption(f"Voice-first AI assistant for **{STORE_PROFILE['name']}** · {STORE_PROFILE['address']}")
with col_h2:
    mode = "🟢 LIVE (Claude API)" if not DEMO_MODE else "🟡 DEMO mode (no API key)"
    st.markdown(f"**Mode:** {mode}")
    cal = get_calendar_context()
    if cal["upcoming_festivals"]:
        nf = cal["upcoming_festivals"][0]
        st.markdown(f"📅 **{nf['name']}** in {nf['days_away']} days")

st.divider()

# Sidebar — live state
with st.sidebar:
    st.subheader("📦 Live Inventory")
    low_stock = [
        (sku, st.session_state.inventory.get(sku["sku_id"], 0))
        for sku in SKU_CATALOG
        if st.session_state.inventory.get(sku["sku_id"], 0) <= 10
    ]
    if low_stock:
        st.warning(f"{len(low_stock)} items at low stock")
        for sku, stock in low_stock:
            st.markdown(f"- {sku['name'].split()[0]}: **{stock}**")
    else:
        st.success("All stock levels healthy")

    st.divider()
    st.subheader("💡 Try saying...")
    for s in DEMO_SUGGESTIONS:
        if st.button(s, key=f"suggest_{hash(s)}"):
            st.session_state.messages.append({"role": "user", "content": s})
            with st.spinner("Thinking..."):
                reply = process_owner_command(s)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

    st.divider()
    st.caption(
        "🟡 In DEMO mode, no API calls are made — responses come from heuristic logic. "
        "Set `ANTHROPIC_API_KEY` env var to enable LIVE mode."
    )

# Main chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
user_input = st.chat_input("Boliye... (Tamil/Hindi/English code-mixed OK)")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = process_owner_command(user_input)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
