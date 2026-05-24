# DukaanAI — API Specification (v0.1)

> REST contracts for the agent layer. Every endpoint maps 1:1 to a specialist agent. Schemas are auto-derived from `schemas.py` (Pydantic v2), so this document and the runtime are guaranteed to agree.

**Base URL (pilot):** `https://api.dukaan.ai/v1`
**Auth:** Bearer token (`Authorization: Bearer <store_jwt>`) — JWT carries `store_id`, `trust_level`, `po_ceiling_inr`.
**Errors:** RFC 7807 problem+json. Validation errors return HTTP 422 with the failing Pydantic field path.
**Idempotency:** POSTs accept an `Idempotency-Key` header. Replays within 24h return the original response.

---

## 1. `POST /v1/parse-voice` — Voice Parser Agent

Convert a raw transcript (any of Tamil / Hindi / English / code-mixed) into a structured action.

### Request
```json
{
  "transcript": "Anna do kilo sugar customer ko de diya UPI mein",
  "store_id": "STR-042",
  "context": {
    "recent_skus": ["SKU-007", "SKU-014"],
    "last_customer": null
  }
}
```

### Response → `VoiceParseOutput`
```json
{
  "intent": "LOG_SALE",
  "confidence": 0.92,
  "items": [
    {
      "colloquial_name": "sugar",
      "matched_sku_id": "SKU-007",
      "matched_sku_name": "Sugar 1kg",
      "match_confidence": 0.95,
      "quantity": 2,
      "unit": "kg"
    }
  ],
  "customer_reference": null,
  "payment_mode": "upi",
  "clarification_needed": false,
  "raw_language_detected": "mixed",
  "reasoning": "Detected LOG_SALE — 'de diya' = past-tense sale; quantity 'do kilo' = 2kg; UPI explicit."
}
```

### Failure modes
| HTTP | Reason |
|---|---|
| 422 | Transcript empty or > 500 chars |
| 200 + `clarification_needed=true` | Ambiguous item — owner must disambiguate |
| 200 + `intent="UNCLEAR"` | Could not infer action; UI shows the raw transcript back to owner |

---

## 2. `POST /v1/forecast-replenishment` — Replenishment Forecast Agent

Returns a ranked reorder list with festival-aware demand multipliers.

### Request
```json
{
  "store_id": "STR-042",
  "forecast_horizon_days": 7,
  "include_categories": null,
  "min_priority": "MEDIUM"
}
```

### Response → `ReplenishmentForecastOutput`
```json
{
  "forecast_date": "2026-05-22",
  "store_id": "STR-042",
  "recommendations": [
    {
      "sku_id": "SKU-007",
      "sku_name": "Sugar 1kg",
      "priority": "CRITICAL",
      "current_stock": 4,
      "daily_velocity": 3.8,
      "days_of_cover": 1.1,
      "recommended_order_qty": 30,
      "recommended_supplier": "SUP-002",
      "confidence": 0.88,
      "reasoning": "Velocity 3.8/day, only 1.1 days cover. Eid al-Adha in 5 days → +20% sugar demand expected.",
      "festival_factor_applied": "Eid al-Adha (+20%)"
    }
  ],
  "summary": "3 critical, 5 high-priority items. ₹12,400 estimated PO value.",
  "data_gaps": [],
  "total_estimated_order_value_inr": 12400.0
}
```

### Notes for integrators
- Daily velocity = trailing 14-day window, excluding stockout days.
- Festival multipliers are derived from `calendar.festivals` × `category.festival_sensitivity`.
- `data_gaps` is populated when a SKU has < 5 sales records — confidence is capped at 0.6 in that case.

---

## 3. `POST /v1/generate-invoice` — Invoice Agent

GST-compliant invoice generation. CGST+SGST for intra-state, IGST for inter-state (auto-detected from state codes).

### Request
```json
{
  "store_id": "STR-042",
  "customer": {
    "name": "Rajesh Traders",
    "phone": "+919876543210",
    "gstin": "33AABCR1234C1Z5",
    "state_code": "33",
    "is_b2b": true
  },
  "line_items_input": [
    { "sku_id": "SKU-007", "quantity": 5, "discount_pct": 0 },
    { "sku_id": "SKU-014", "quantity": 2, "discount_pct": 5 }
  ],
  "payment_mode": "credit"
}
```

### Response → `InvoiceOutput`
```json
{
  "invoice_number": "INV/2026-27/00142",
  "invoice_date": "2026-05-22",
  "invoice_time": "11:42",
  "store": { "name": "Sri Lakshmi Stores", "gstin": "33AAAPL1234C1Z5", "address": "...", "state_code": "33" },
  "customer": { "name": "Rajesh Traders", "gstin": "33AABCR1234C1Z5", "state_code": "33", "is_b2b": true },
  "line_items": [
    {
      "sku_id": "SKU-007",
      "sku_name": "Sugar 1kg",
      "hsn_code": "1701",
      "quantity": 5,
      "unit_price": 48.0,
      "discount_pct": 0,
      "taxable_value": 240.0,
      "gst_rate": 5,
      "cgst_amount": 6.0,
      "sgst_amount": 6.0,
      "igst_amount": 0,
      "line_total": 252.0
    }
  ],
  "totals": {
    "subtotal_taxable": 540.0,
    "total_cgst": 13.5,
    "total_sgst": 13.5,
    "total_igst": 0,
    "round_off": 0,
    "grand_total": 567.0,
    "amount_in_words": "Five Hundred Sixty Seven Rupees Only"
  },
  "payment_mode": "credit",
  "irn_required": true,
  "validation_errors": [],
  "owner_facing_summary": "Invoice ₹567 for Rajesh Traders generated. Credit sale — added to ledger."
}
```

### Validation rules enforced server-side
- Store and customer state codes equal → CGST/SGST split. Different → IGST.
- B2B invoice with grand_total > ₹50,000 → `irn_required=true` (e-invoicing trigger).
- Any line item missing HSN code → 422.

---

## 4. `POST /v1/draft-po` — Supplier PO Agent

Draft a purchase order. May be triggered by voice ("Anna ko 50 packet Maggi bhej do bolo") or by accepted replenishment recommendations.

### Request
```json
{
  "store_id": "STR-042",
  "supplier_id": "SUP-002",
  "source": "owner_specified",
  "items": [
    { "sku_id": "SKU-007", "quantity": 30 },
    { "sku_id": "SKU-019", "quantity": 50 }
  ],
  "owner_note": "Anna se bolna friday tak chahiye"
}
```

### Response → `SupplierPOOutput`
```json
{
  "po_number": "PO/2026-05/0087",
  "po_date": "2026-05-22",
  "supplier": {
    "supplier_id": "SUP-002",
    "name": "Anna Wholesale",
    "contact_phone": "+919812345678",
    "expected_delivery_date": "2026-05-25"
  },
  "line_items": [
    {
      "sku_id": "SKU-007",
      "sku_name": "Sugar 1kg",
      "quantity": 30,
      "unit": "kg",
      "last_known_price": 42.0,
      "price_confirmation_needed": false,
      "estimated_line_total": 1260.0,
      "source": "owner_specified",
      "moq_validated": true
    }
  ],
  "totals": { "estimated_subtotal": 3760.0, "estimated_gst": 188.0, "estimated_grand_total": 3948.0 },
  "requires_owner_approval": false,
  "approval_reason": null,
  "owner_facing_summary": "PO of ₹3,948 ready for Anna Wholesale. Send via WhatsApp?",
  "supplier_facing_message": "Namaste Anna ji — order chahiye Friday tak: 30kg Sugar, 50 Maggi packets. Total ~₹3,948. Confirm karo.",
  "notes_to_owner": []
}
```

### Approval gate
- If `estimated_grand_total > store.po_ceiling_inr` (default ₹50,000 at trust Level 3, ₹10,000 at Level 2), `requires_owner_approval=true` and the supplier message is **not** auto-sent.

---

## 5. `POST /v1/chat` — Conversational Router

The single entry point used by the owner-facing UI. Handles orchestration, trust-level enforcement, and natural-language reply formatting. Internally calls the four agents above.

### Request
```json
{
  "store_id": "STR-042",
  "owner_message": "Kal raat ka sale total dikha aur sugar ka stock kitna bacha hai",
  "conversation_id": "conv_4f8c..."
}
```

### Response → `RouterOutput`
```json
{
  "tool_calls": [
    { "tool": "sales_history_lookup", "args": { "from": "2026-05-21T18:00", "to": "2026-05-22T03:00" } },
    { "tool": "inventory_lookup", "args": { "sku_ids": ["SKU-007"] } }
  ],
  "reply_to_owner": "Kal raat 6 baje se ab tak ₹4,820 ka sale — 23 bills. Sugar stock: 4 kg bacha hai (1 din mein khatam ho jayega, order karna padega).",
  "trust_action_required": "auto_execute",
  "internal_note": "Read-only query. No state changes."
}
```

### Trust-action semantics
| Value | UI behavior |
|---|---|
| `auto_execute` | Tool calls already ran; reply is final. |
| `confirm_first` | Reply contains the proposed action. UI shows ✅ / ❌ buttons. Action runs on ✅. |
| `block_pending_review` | High-risk action (e.g., > po_ceiling). Reply explains why and asks for explicit confirmation phrase. |

---

## 6. Webhooks (outbound)

| Event | Fires when | Payload |
|---|---|---|
| `sale.logged` | `LOG_SALE` action confirmed | Sale record + updated stock |
| `invoice.generated` | Invoice created | `InvoiceOutput` |
| `po.sent` | Supplier message dispatched | `SupplierPOOutput` + delivery channel |
| `stockout.imminent` | Forecast detects < 1 day cover | `ReplenishmentRecommendation` |

Subscribers: accountant CA portal, Tally export, supplier ERP (if any).

---

## 7. Rate limits & SLOs

| Endpoint | p50 latency | p95 latency | RPS per store |
|---|---|---|---|
| `/parse-voice` | 600 ms | 1.2 s | 2 |
| `/forecast-replenishment` | 1.5 s | 3.0 s | 0.1 |
| `/generate-invoice` | 800 ms | 1.5 s | 1 |
| `/draft-po` | 1.0 s | 2.0 s | 0.3 |
| `/chat` | 1.2 s | 2.5 s | 3 |

Internal target: **end-to-end voice → confirmed sale logged in < 3 seconds** (K3 from the PRD).

---

## 8. Versioning

- Breaking changes → new path prefix (`/v2`).
- Additive changes (new optional fields) → same version, documented in changelog.
- Prompt versions are pinned per release (`X-Prompt-Version: voice_parser@v0.3`) so downstream eval harnesses can attribute regressions.
