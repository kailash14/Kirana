"""
Seed data for the DukaanAI demo.

Generates a realistic kirana store profile with:
  - 25 SKUs across categories
  - 5 suppliers
  - 90 days of synthetic but realistic sales history
  - Calendar context (today + nearest festivals)
"""

from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(42)


# ============================================================
# Store profile
# ============================================================

STORE_PROFILE = {
    "store_id": "STR-042",
    "code": "SLS",
    "name": "Sri Lakshmi Stores",
    "gstin": "33AAAPL1234C1Z5",
    "address": "12, Anna Salai, Adyar, Chennai 600020",
    "state_code": "33",
    "po_ceiling_inr": 50000,
    "trust_level": 2,
    "preferred_language": "mixed",
}


# ============================================================
# SKU catalog
# ============================================================

SKU_CATALOG = [
    # Staples
    {"sku_id": "SKU-001", "name": "Aashirvaad Atta 5kg", "aliases": ["atta", "wheat flour", "aata"],
     "hsn": "1101", "gst_rate": 0, "mrp": 270, "selling_price": 270,
     "category": "atta", "primary_supplier_id": "SUP-021"},
    {"sku_id": "SKU-002", "name": "Pillsbury Atta 5kg", "aliases": ["pillsbury atta"],
     "hsn": "1101", "gst_rate": 0, "mrp": 265, "selling_price": 265,
     "category": "atta", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-003", "name": "India Gate Basmati Rice 5kg", "aliases": ["basmati", "rice", "chawal"],
     "hsn": "1006", "gst_rate": 5, "mrp": 750, "selling_price": 750,
     "category": "rice", "primary_supplier_id": "SUP-023"},
    {"sku_id": "SKU-004", "name": "Sona Masoori Rice 10kg", "aliases": ["sona masoori"],
     "hsn": "1006", "gst_rate": 5, "mrp": 580, "selling_price": 580,
     "category": "rice", "primary_supplier_id": "SUP-023"},
    {"sku_id": "SKU-005", "name": "Toor Dal 1kg", "aliases": ["toor", "arhar", "thuvaram paruppu"],
     "hsn": "0713", "gst_rate": 0, "mrp": 165, "selling_price": 165,
     "category": "dal", "primary_supplier_id": "SUP-023"},
    {"sku_id": "SKU-006", "name": "Tata Salt 1kg", "aliases": ["salt", "namak", "uppu"],
     "hsn": "2501", "gst_rate": 5, "mrp": 28, "selling_price": 28,
     "category": "staple", "primary_supplier_id": "SUP-024"},

    # Oil & Ghee
    {"sku_id": "SKU-007", "name": "Fortune Sunflower Oil 1L", "aliases": ["fortune oil", "sunflower oil", "tel"],
     "hsn": "1512", "gst_rate": 5, "mrp": 165, "selling_price": 165,
     "category": "oil", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-008", "name": "Saffola Gold Oil 1L", "aliases": ["saffola"],
     "hsn": "1512", "gst_rate": 5, "mrp": 185, "selling_price": 185,
     "category": "oil", "primary_supplier_id": "SUP-024"},
    {"sku_id": "SKU-009", "name": "Amul Ghee 1L", "aliases": ["ghee", "amul ghee", "nei"],
     "hsn": "0405", "gst_rate": 12, "mrp": 670, "selling_price": 670,
     "category": "ghee", "primary_supplier_id": "SUP-025"},

    # Snacks
    {"sku_id": "SKU-010", "name": "Maggi 2-Minute Noodles 70g", "aliases": ["maggi", "noodles"],
     "hsn": "1902", "gst_rate": 18, "mrp": 14, "selling_price": 14,
     "category": "snacks", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-011", "name": "Maggi Masala Cup Noodles", "aliases": ["maggi cup"],
     "hsn": "1902", "gst_rate": 18, "mrp": 50, "selling_price": 50,
     "category": "snacks", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-012", "name": "Lays Magic Masala 52g", "aliases": ["lays", "chips"],
     "hsn": "2005", "gst_rate": 12, "mrp": 20, "selling_price": 20,
     "category": "snacks", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-013", "name": "Britannia Marie Gold 250g", "aliases": ["marie biscuit", "biscuit"],
     "hsn": "1905", "gst_rate": 18, "mrp": 30, "selling_price": 30,
     "category": "biscuit", "primary_supplier_id": "SUP-022"},

    # Beverages
    {"sku_id": "SKU-014", "name": "Red Label Tea 500g", "aliases": ["tea", "chai", "red label"],
     "hsn": "0902", "gst_rate": 5, "mrp": 280, "selling_price": 280,
     "category": "beverage", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-015", "name": "Bru Instant Coffee 100g", "aliases": ["bru", "coffee"],
     "hsn": "0901", "gst_rate": 18, "mrp": 320, "selling_price": 320,
     "category": "beverage", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-016", "name": "Coca-Cola 2L", "aliases": ["coke", "cola"],
     "hsn": "2202", "gst_rate": 28, "mrp": 105, "selling_price": 105,
     "category": "beverage", "primary_supplier_id": "SUP-025"},

    # Dairy
    {"sku_id": "SKU-017", "name": "Aavin Milk 500ml", "aliases": ["milk", "paal", "aavin"],
     "hsn": "0401", "gst_rate": 0, "mrp": 28, "selling_price": 28,
     "category": "dairy", "primary_supplier_id": "SUP-025"},
    {"sku_id": "SKU-018", "name": "Amul Butter 100g", "aliases": ["butter", "makhan"],
     "hsn": "0405", "gst_rate": 12, "mrp": 56, "selling_price": 56,
     "category": "dairy", "primary_supplier_id": "SUP-025"},

    # Sugar/Sweet
    {"sku_id": "SKU-019", "name": "Madhur Sugar 1kg", "aliases": ["sugar", "cheeni", "sakkarai"],
     "hsn": "1701", "gst_rate": 5, "mrp": 48, "selling_price": 48,
     "category": "sugar", "primary_supplier_id": "SUP-024"},
    {"sku_id": "SKU-020", "name": "Patanjali Jaggery Powder 500g", "aliases": ["jaggery", "vellam", "gur"],
     "hsn": "1701", "gst_rate": 5, "mrp": 75, "selling_price": 75,
     "category": "sugar", "primary_supplier_id": "SUP-021"},

    # Patanjali
    {"sku_id": "SKU-021", "name": "Patanjali Atta Noodles", "aliases": ["patanjali noodles"],
     "hsn": "1902", "gst_rate": 18, "mrp": 15, "selling_price": 15,
     "category": "snacks", "primary_supplier_id": "SUP-021"},
    {"sku_id": "SKU-022", "name": "Patanjali Honey 500g", "aliases": ["honey", "shahad"],
     "hsn": "0409", "gst_rate": 0, "mrp": 175, "selling_price": 175,
     "category": "premium", "primary_supplier_id": "SUP-021"},
    {"sku_id": "SKU-023", "name": "Patanjali Dish Wash Bar", "aliases": ["dishwash"],
     "hsn": "3401", "gst_rate": 18, "mrp": 25, "selling_price": 25,
     "category": "household", "primary_supplier_id": "SUP-021"},

    # Personal care
    {"sku_id": "SKU-024", "name": "Colgate Toothpaste 100g", "aliases": ["colgate", "toothpaste"],
     "hsn": "3306", "gst_rate": 18, "mrp": 65, "selling_price": 65,
     "category": "personal", "primary_supplier_id": "SUP-022"},
    {"sku_id": "SKU-025", "name": "Lux Soap 100g", "aliases": ["soap", "lux"],
     "hsn": "3401", "gst_rate": 18, "mrp": 35, "selling_price": 35,
     "category": "personal", "primary_supplier_id": "SUP-022"},
]


# ============================================================
# Suppliers
# ============================================================

SUPPLIERS = [
    {
        "supplier_id": "SUP-021",
        "name": "Patanjali Distributor Chennai",
        "contact_phone": "+91-9876543210",
        "lead_time_days": 4,
        "moq_default": 5,
        "sku_ids_carried": ["SKU-001", "SKU-020", "SKU-021", "SKU-022", "SKU-023"],
    },
    {
        "supplier_id": "SUP-022",
        "name": "Metro Cash & Carry",
        "contact_phone": "+91-9876543211",
        "lead_time_days": 2,
        "moq_default": 6,
        "sku_ids_carried": [
            "SKU-002", "SKU-007", "SKU-010", "SKU-011", "SKU-012",
            "SKU-013", "SKU-014", "SKU-015", "SKU-024", "SKU-025",
        ],
    },
    {
        "supplier_id": "SUP-023",
        "name": "Bharat Grains Wholesale",
        "contact_phone": "+91-9876543212",
        "lead_time_days": 5,
        "moq_default": 10,
        "sku_ids_carried": ["SKU-003", "SKU-004", "SKU-005"],
    },
    {
        "supplier_id": "SUP-024",
        "name": "Annapurna Distributors",
        "contact_phone": "+91-9876543213",
        "lead_time_days": 3,
        "moq_default": 5,
        "sku_ids_carried": ["SKU-006", "SKU-008", "SKU-019"],
    },
    {
        "supplier_id": "SUP-025",
        "name": "Local Dairy & Beverages",
        "contact_phone": "+91-9876543214",
        "lead_time_days": 1,
        "moq_default": 3,
        "sku_ids_carried": ["SKU-009", "SKU-016", "SKU-017", "SKU-018"],
    },
]


# ============================================================
# Current inventory (snapshot today)
# ============================================================

CURRENT_INVENTORY = {
    "SKU-001": 12,  # atta — low
    "SKU-002": 18,
    "SKU-003": 8,
    "SKU-004": 14,
    "SKU-005": 22,
    "SKU-006": 45,
    "SKU-007": 6,   # oil — critical
    "SKU-008": 11,
    "SKU-009": 9,
    "SKU-010": 32,
    "SKU-011": 8,   # maggi cup — low
    "SKU-012": 24,
    "SKU-013": 18,
    "SKU-014": 7,
    "SKU-015": 12,
    "SKU-016": 16,
    "SKU-017": 28,
    "SKU-018": 11,
    "SKU-019": 19,
    "SKU-020": 14,
    "SKU-021": 22,
    "SKU-022": 5,   # honey — low
    "SKU-023": 30,
    "SKU-024": 24,
    "SKU-025": 38,
}


# ============================================================
# Synthetic 30-day sales history (per SKU)
# ============================================================

def _generate_30d_sales(base_velocity: float, volatility: float = 0.3) -> list[int]:
    """Generate plausible daily sales for an SKU with weekend bump."""
    sales = []
    for i in range(30):
        day_of_week = i % 7  # 0=Mon ... 6=Sun for synthetic purposes
        weekend_mult = 1.4 if day_of_week >= 5 else 1.0
        noise = random.uniform(1 - volatility, 1 + volatility)
        raw = base_velocity * weekend_mult * noise
        sales.append(max(0, round(raw)))
    return sales


_VELOCITY_MAP = {
    "SKU-001": 4.6, "SKU-002": 2.1, "SKU-003": 1.4, "SKU-004": 2.8, "SKU-005": 3.2,
    "SKU-006": 6.8, "SKU-007": 2.6, "SKU-008": 1.8, "SKU-009": 1.1, "SKU-010": 8.4,
    "SKU-011": 2.2, "SKU-012": 5.6, "SKU-013": 4.1, "SKU-014": 3.5, "SKU-015": 2.0,
    "SKU-016": 3.8, "SKU-017": 12.4, "SKU-018": 3.2, "SKU-019": 4.8, "SKU-020": 1.9,
    "SKU-021": 1.6, "SKU-022": 0.8, "SKU-023": 1.2, "SKU-024": 2.6, "SKU-025": 4.2,
}


SALES_HISTORY = []
for sku in SKU_CATALOG:
    sku_id = sku["sku_id"]
    velocity = _VELOCITY_MAP.get(sku_id, 1.0)
    SALES_HISTORY.append(
        {
            "sku_id": sku_id,
            "sku_name": sku["name"],
            "last_30d": _generate_30d_sales(velocity),
            "supplier_lead_days": next(
                (s["lead_time_days"] for s in SUPPLIERS if s["supplier_id"] == sku["primary_supplier_id"]),
                3,
            ),
            "supplier": next(
                (s["name"] for s in SUPPLIERS if s["supplier_id"] == sku["primary_supplier_id"]),
                None,
            ),
            "est_unit_price": sku["mrp"] * 0.92,  # supplier price ~ 8% margin
        }
    )


# ============================================================
# Calendar context (today + festivals)
# ============================================================

def get_calendar_context() -> dict:
    today = date.today()
    # Static festival calendar for demo
    festivals = [
        {"name": "Eid al-Adha", "date": "2026-05-27"},
        {"name": "Ratha Yatra", "date": "2026-06-26"},
        {"name": "Raksha Bandhan", "date": "2026-08-28"},
        {"name": "Diwali", "date": "2026-11-09"},
        {"name": "Christmas", "date": "2026-12-25"},
        {"name": "Pongal", "date": "2027-01-14"},
    ]
    upcoming = []
    for f in festivals:
        f_date = datetime.strptime(f["date"], "%Y-%m-%d").date()
        days_away = (f_date - today).days
        if 0 <= days_away <= 60:
            upcoming.append({"name": f["name"], "date": f["date"], "days_away": days_away})
    return {
        "today": str(today),
        "day_of_week": today.strftime("%A"),
        "upcoming_festivals": upcoming,
    }


# ============================================================
# Initial demo conversation seed
# ============================================================

DEMO_SUGGESTIONS = [
    "Aashirvaad atta paanch packet Kumar uncle ko bika, cash mein",
    "Kitna Maggi bacha hai stock mein?",
    "Patanjali wale ko order bhejo",
    "Diwali ke liye kya order karu?",
    "Kumar uncle ka bill banao",
    "Aaj Fortune Oil 3 litre Sharma ji ne UPI mein liya",
]


# ============================================================
# Helpers for persistence
# ============================================================

def write_seed_files(data_dir: Path):
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "store_profile.json").write_text(json.dumps(STORE_PROFILE, indent=2))
    (data_dir / "sku_catalog.json").write_text(json.dumps(SKU_CATALOG, indent=2))
    (data_dir / "suppliers.json").write_text(json.dumps(SUPPLIERS, indent=2))
    (data_dir / "current_inventory.json").write_text(json.dumps(CURRENT_INVENTORY, indent=2))
    (data_dir / "sales_history.json").write_text(json.dumps(SALES_HISTORY, indent=2))


if __name__ == "__main__":
    out = Path(__file__).parent / "data"
    write_seed_files(out)
    print(f"Wrote seed data to {out}")
    print(f"  - {len(SKU_CATALOG)} SKUs")
    print(f"  - {len(SUPPLIERS)} suppliers")
    print(f"  - {len(SALES_HISTORY)} SKU sales histories")
    print(f"  - Today: {get_calendar_context()}")
