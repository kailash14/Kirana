# Wireframes (low-fidelity)

> Pre-design sketches for the three core screens. Final visual design happens in Figma during weeks 3-4 of the pilot. These wireframes lock down information architecture and interaction patterns first.

---

## Screen 1 — Chat (the primary surface)

Phone, portrait. Owner spends 90% of their time here.

```
┌──────────────────────────────────────┐
│ ☰  DukaanAI       Sri Lakshmi  ⚙️    │  <- Header: store name + settings
├──────────────────────────────────────┤
│ 🌅 Good morning, Murugan anna        │  <- Morning brief card
│ ┌────────────────────────────────┐   │
│ │ 3 items low                    │   │
│ │ Eid in 5d → sugar demand +20%  │   │
│ │ Yesterday: ₹8,420 (32 bills)   │   │
│ │              [Review forecast] │   │
│ └────────────────────────────────┘   │
│                                      │
│         11:42 AM                     │
│   ┌──────────────────────────┐       │
│   │ Anna do kilo sugar       │       │  <- Owner's voice msg (right-align)
│   │ customer ko de diya UPI  │       │
│   └──────────────────────────┘ 🎙️    │
│                                      │
│ ✓ Logged                             │  <- Inline confirmation (auto-exec L2+)
│ ┌────────────────────────────────┐   │
│ │ 2 kg Sugar — ₹96 — UPI         │   │
│ │ Stock left: 2 kg ⚠️             │   │
│ │ [Undo]              [Details]  │   │  <- 30-sec undo window
│ └────────────────────────────────┘   │
│                                      │
│         11:43 AM                     │
│ 💡 Sugar will stockout by tomorrow.  │  <- Proactive suggestion
│    Order 30 kg from Anna Wholesale?  │
│    [Yes, draft PO]    [Not now]      │
│                                      │
├──────────────────────────────────────┤
│  🎙️  Tap to speak  or type...        │  <- Big tappable mic
└──────────────────────────────────────┘
   ↑                                   ↑
   Voice-first; keyboard secondary     Dashboard tab (≡ menu)
```

### Interaction rules
- **Right-aligned bubbles** = owner. **Left-aligned cards** = DukaanAI.
- Voice messages show transcript inline — never hide what the AI heard.
- Every auto-executed action has a **30-second Undo**. After 30s, owner must voice a reversal.
- Confidence < 0.85 → no auto-execute, even at trust Level 3. UI shows ✅/❌ buttons.
- **Code-mix preserved.** We don't translate the owner's words back at them.

---

## Screen 2 — Dashboard (glance-only)

Accessed via ☰ menu. Read-only summary; all *actions* happen in chat.

```
┌──────────────────────────────────────┐
│ ← Dashboard                          │
├──────────────────────────────────────┤
│  Today        Week         Month     │  <- Tabs
│  ─────                               │
│                                      │
│  ₹4,820                               │  <- Big number, today's sales
│  23 bills · 18 cash · 5 UPI          │
│                                      │
│  ┌────────────────────────────────┐   │
│  │ ▁▂▃▅▇▇▆▄▂  Hourly sales       │   │  <- Sparkline
│  └────────────────────────────────┘   │
│                                      │
│  🔴 Stockout risk (3)                │
│  • Sugar 1kg     —  1.1 days cover   │
│  • Maggi 70g     —  0.8 days cover   │
│  • Atta 5kg      —  0.6 days cover   │
│              [View full forecast →]  │
│                                      │
│  💰 Credit ledger                    │
│  Outstanding: ₹12,450 (8 names)      │
│              [View ledger →]         │
│                                      │
│  📊 Top movers today                 │
│  1. Sugar 1kg     ₹820 (17 units)    │
│  2. Tea 250g      ₹640 (8 units)     │
│  3. Maggi 70g     ₹420 (35 units)    │
└──────────────────────────────────────┘
```

### Design rules
- No charts that need explanation. Sparklines only. Numbers + words first.
- Every metric is a tap → opens chat with that context pre-loaded.
  Example: tap "Outstanding ₹12,450" → chat asks "Want a credit reminder list?"

---

## Screen 3 — Invoice preview

Triggered after invoice generation. Owner reviews, shares via WhatsApp, or prints.

```
┌──────────────────────────────────────┐
│ ← Invoice  INV/2026-27/00142   ⋮     │
├──────────────────────────────────────┤
│           SRI LAKSHMI STORES         │
│       12 Anna Salai, Chennai 600002  │
│        GSTIN: 33AAAPL1234C1Z5        │
├──────────────────────────────────────┤
│ Bill to:  Rajesh Traders             │
│           GSTIN: 33AABCR1234C1Z5     │
│ Date:     22-May-2026  11:42         │
│ Payment:  Credit                     │
├──────────────────────────────────────┤
│ #  Item         HSN   Qty  Rate  Amt │
│ 1  Sugar 1kg   1701   5  48.00 240   │
│ 2  Oil 1L      1507   2 280.00 560   │
│    (5% discount on item 2)           │
├──────────────────────────────────────┤
│            Subtotal       ₹  786.00  │
│            CGST  2.5%     ₹   13.50  │
│            SGST  2.5%     ₹   13.50  │
│            CGST  9.0%     ₹   48.00  │
│            SGST  9.0%     ₹   48.00  │
│            Round off      ₹    1.00  │
│            ─────────────────────────  │
│            GRAND TOTAL    ₹  910.00  │
│  In words: Nine Hundred Ten Rupees   │
│                                      │
│  ⚠️ B2B > ₹50K threshold not crossed │
│     IRN not required                 │
├──────────────────────────────────────┤
│ [📱 WhatsApp]  [🖨️ Print]  [⬇️ PDF] │
└──────────────────────────────────────┘
```

### Notes
- All GST math is visible — the owner gains trust by seeing the numbers.
- IRN trigger is shown explicitly (the system *tells* the owner whether e-invoicing is needed, instead of silently doing or not doing it).
- Share buttons are dumb pass-throughs (WhatsApp Business API / system PDF / system print intent). Nothing custom.

---

## What's intentionally **not** in the MVP

- **No dashboard editing.** Numbers are derived from chat actions, period.
- **No multi-user roles.** Pilot is single-owner per store. Cashier mode → v2.
- **No customer-facing app.** Customers receive SMS/WhatsApp from the owner — they never log in.
- **No barcode scanning.** Voice replaces it. (Re-evaluate post-pilot if categories like pharma require it.)
