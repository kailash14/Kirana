"""
Pydantic v2 schemas for DukaanAI agent inputs and outputs.

Every agent in the system reads and writes against these schemas, which serves as:
  1. Runtime validation against LLM hallucinations / malformed JSON
  2. Living API documentation (Pydantic auto-generates JSON schemas)
  3. Type-safety contract between agents

Mirrors the Feature Gate architecture pattern.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# Shared enums
# ============================================================


class Intent(str, Enum):
    LOG_SALE = "LOG_SALE"
    LOG_RECEIPT = "LOG_RECEIPT"
    CHECK_STOCK = "CHECK_STOCK"
    GENERATE_INVOICE = "GENERATE_INVOICE"
    DRAFT_PO = "DRAFT_PO"
    FORECAST_QUERY = "FORECAST_QUERY"
    ADJUST_STOCK = "ADJUST_STOCK"
    UNCLEAR = "UNCLEAR"


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PaymentMode(str, Enum):
    CASH = "cash"
    UPI = "upi"
    CREDIT = "credit"
    CARD = "card"


class TrustLevel(int, Enum):
    LEVEL_1_NEW = 1
    LEVEL_2_FAMILIAR = 2
    LEVEL_3_TRUSTED = 3


# ============================================================
# Voice Parser Agent I/O
# ============================================================


class ParsedItem(BaseModel):
    colloquial_name: str
    matched_sku_id: str | None = None
    matched_sku_name: str | None = None
    match_confidence: float = Field(ge=0.0, le=1.0)
    quantity: float = 0
    unit: str | None = None


class VoiceParseOutput(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    items: list[ParsedItem] = []
    customer_reference: str | None = None
    supplier_reference: str | None = None
    payment_mode: PaymentMode | None = None
    clarification_needed: bool = False
    clarification_question: str | None = None
    raw_language_detected: Literal["ta", "hi", "en", "mixed"] = "mixed"
    reasoning: str = ""


# ============================================================
# Replenishment Forecast Agent I/O
# ============================================================


class ReplenishmentRecommendation(BaseModel):
    sku_id: str
    sku_name: str
    priority: Priority
    current_stock: int
    daily_velocity: float
    days_of_cover: float
    recommended_order_qty: int
    recommended_supplier: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    festival_factor_applied: str | None = None


class ReplenishmentForecastOutput(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    forecast_date: str  # YYYY-MM-DD
    store_id: str
    recommendations: list[ReplenishmentRecommendation]
    summary: str
    data_gaps: list[str] = []
    total_estimated_order_value_inr: float = 0.0


# ============================================================
# Invoice Agent I/O
# ============================================================


class StoreProfile(BaseModel):
    name: str
    gstin: str
    address: str
    state_code: str


class CustomerProfile(BaseModel):
    name: str = "Walk-in Customer"
    phone: str | None = None
    gstin: str | None = None
    state_code: str | None = None
    is_b2b: bool = False


class InvoiceLineItem(BaseModel):
    sku_id: str
    sku_name: str
    hsn_code: str
    quantity: float
    unit_price: float
    discount_pct: float = 0.0
    taxable_value: float
    gst_rate: float
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    line_total: float


class InvoiceTotals(BaseModel):
    subtotal_taxable: float
    total_cgst: float = 0.0
    total_sgst: float = 0.0
    total_igst: float = 0.0
    round_off: float = 0.0
    grand_total: float
    amount_in_words: str


class InvoiceOutput(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    invoice_number: str
    invoice_date: str
    invoice_time: str
    store: StoreProfile
    customer: CustomerProfile
    line_items: list[InvoiceLineItem]
    totals: InvoiceTotals
    payment_mode: PaymentMode
    irn_required: bool = False
    validation_errors: list[str] = []
    owner_facing_summary: str


# ============================================================
# Supplier PO Agent I/O
# ============================================================


class POSupplier(BaseModel):
    supplier_id: str
    name: str
    contact_phone: str
    expected_delivery_date: str


class POLineItem(BaseModel):
    sku_id: str
    sku_name: str
    quantity: int
    unit: str
    last_known_price: float
    price_confirmation_needed: bool = False
    estimated_line_total: float
    source: Literal["owner_specified", "replenishment_forecast", "historical_pattern"]
    moq_validated: bool = True


class POTotals(BaseModel):
    estimated_subtotal: float
    estimated_gst: float
    estimated_grand_total: float


class SupplierPOOutput(BaseModel):
    po_number: str
    po_date: str
    supplier: POSupplier
    line_items: list[POLineItem]
    totals: POTotals
    requires_owner_approval: bool = False
    approval_reason: str | None = None
    clarification_needed: bool = False
    clarification_question: str | None = None
    owner_facing_summary: str
    supplier_facing_message: str
    notes_to_owner: list[str] = []


# ============================================================
# Conversational Router I/O
# ============================================================


class ToolCall(BaseModel):
    tool: Literal[
        "voice_parser",
        "inventory_lookup",
        "invoice_agent",
        "replenishment_forecast",
        "supplier_po_agent",
        "sales_history_lookup",
        "none",
    ]
    args: dict = {}


class RouterOutput(BaseModel):
    tool_calls: list[ToolCall] = []
    reply_to_owner: str
    trust_action_required: Literal[
        "auto_execute", "confirm_first", "block_pending_review"
    ] = "confirm_first"
    internal_note: str = ""


# ============================================================
# Domain entities (state)
# ============================================================


class SKU(BaseModel):
    sku_id: str
    name: str
    aliases: list[str] = []  # colloquial names
    hsn_code: str
    gst_rate: float  # 0, 5, 12, 18, 28
    mrp: float
    selling_price: float
    category: str  # for festival multipliers
    primary_supplier_id: str | None = None


class Supplier(BaseModel):
    supplier_id: str
    name: str
    contact_phone: str
    lead_time_days: int = 3
    moq_default: int = 1
    sku_ids_carried: list[str] = []


class Store(BaseModel):
    store_id: str
    profile: StoreProfile
    trust_level: TrustLevel = TrustLevel.LEVEL_1_NEW
    po_ceiling_inr: float = 50000.0
    preferred_language: Literal["ta", "hi", "en", "mixed"] = "mixed"


class SaleRecord(BaseModel):
    sale_id: str
    timestamp: datetime
    store_id: str
    items: list[ParsedItem]
    customer_reference: str | None = None
    payment_mode: PaymentMode
    invoice_number: str | None = None
    total_inr: float
