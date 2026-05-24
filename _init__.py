# agents/__init__.py
from .voice_parser import parse_voice_command
from .replenishment_forecast import forecast_replenishment
from .invoice_agent import generate_invoice
from .supplier_po_agent import draft_purchase_order
from .base import DEMO_MODE
