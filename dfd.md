# Data Flow Diagrams

## Level 0 — Context Diagram

The system seen from the outside. Who/what touches DukaanAI and what data crosses each boundary.

```mermaid
flowchart LR
    Owner((Store<br/>Owner))
    Customer((Walk-in<br/>Customer))
    Supplier((Supplier<br/>e.g., Anna Wholesale))
    CA((Accountant /<br/>CA))
    GST[GST Portal /<br/>e-Invoice System]
    Bank[Payment<br/>Gateway / UPI]

    System{{DukaanAI<br/>Platform}}

    Owner -- "voice commands,<br/>confirmations" --> System
    System -- "briefs, alerts,<br/>parsed actions" --> Owner

    System -- "GST invoice PDF,<br/>receipt SMS" --> Customer
    Customer -- "(indirectly via owner:<br/>name, phone, GSTIN)" --> System

    System -- "WhatsApp PO message" --> Supplier
    Supplier -- "delivery confirmation,<br/>price changes" --> System

    System -- "monthly export<br/>(Tally / CSV)" --> CA
    CA -- "tax-rule updates,<br/>HSN corrections" --> System

    System <-- "IRN, e-invoice JSON,<br/>filing data" --> GST
    System <-- "UPI status,<br/>settlement" --> Bank

    classDef ext fill:#F3F4F6,stroke:#6B7280,color:#000
    classDef sys fill:#DBEAFE,stroke:#2563EB,color:#000,stroke-width:3px
    class Owner,Customer,Supplier,CA ext
    class GST,Bank ext
    class System sys
```

---

## Level 1 — Internal data flows

Zoom into the platform. Numbered processes (P1–P5) match the five agents.

```mermaid
flowchart TB
    Owner((Owner))

    subgraph Stores["Data Stores"]
        D1[(D1: SKU Catalog)]
        D2[(D2: Inventory)]
        D3[(D3: Sales History)]
        D4[(D4: Supplier Master)]
        D5[(D5: Festival Calendar)]
        D6[(D6: Trust + Audit Log)]
        D7[(D7: Invoice Ledger)]
        D8[(D8: PO Ledger)]
    end

    subgraph Processes["Processes"]
        P0((P0: Router /<br/>Orchestrator))
        P1((P1: Voice Parser))
        P2((P2: Replenishment<br/>Forecast))
        P3((P3: Invoice<br/>Generator))
        P4((P4: PO Drafter))
        P5((P5: Trust Ladder<br/>Evaluator))
    end

    Owner -- "transcript" --> P0
    P0 -- "transcript + context" --> P1
    P1 -- "lookup aliases" --> D1
    P1 -- "parsed action" --> P0

    P0 -- "forecast request" --> P2
    P2 -- "read trailing 14d" --> D3
    P2 -- "read stock levels" --> D2
    P2 -- "read upcoming events" --> D5
    P2 -- "read SKU + category" --> D1
    P2 -- "ranked reorder list" --> P0

    P0 -- "invoice request +<br/>line items" --> P3
    P3 -- "read SKU + HSN + GST rate" --> D1
    P3 -- "decrement stock" --> D2
    P3 -- "append invoice" --> D7
    P3 -- "append sale record" --> D3
    P3 -- "invoice JSON" --> P0

    P0 -- "PO draft request" --> P4
    P4 -- "read supplier + lead time" --> D4
    P4 -- "read last known price" --> D1
    P4 -- "append PO" --> D8
    P4 -- "PO JSON" --> P0

    P0 -- "every action ID +<br/>owner response" --> P5
    P5 -- "update trust level" --> D6
    P5 -- "current trust level" --> P0

    P0 -- "reply +<br/>confirm/auto flag" --> Owner

    classDef store fill:#F5F3FF,stroke:#7C3AED,color:#000
    classDef proc fill:#F0FDF4,stroke:#16A34A,color:#000
    classDef ext fill:#FFF4E6,stroke:#F59E0B,color:#000
    class D1,D2,D3,D4,D5,D6,D7,D8 store
    class P0,P1,P2,P3,P4,P5 proc
    class Owner ext
```

---

## Data dictionary (selected stores)

| Store | Key fields | Update frequency | Retention |
|---|---|---|---|
| **D1 SKU Catalog** | sku_id, name, aliases[], HSN, GST%, MRP, selling_price, category | Weekly (price corrections); Daily (new SKUs during onboarding) | Forever |
| **D2 Inventory** | sku_id, on_hand_qty, last_movement_ts | Every sale, every PO receipt | Forever (snapshots daily) |
| **D3 Sales History** | sale_id, ts, items[], payment_mode, total, invoice_id | Every confirmed sale | 7 years (GST audit) |
| **D5 Festival Calendar** | date, festival_name, applicable_states[], category_multipliers{} | Yearly refresh + manual edits | Forever |
| **D6 Trust + Audit Log** | action_id, owner_id, agent, accepted/rejected, ts | Every owner-facing action | 2 years rolling |

---

## Privacy & data residency

- All data stored in **AWS Mumbai (ap-south-1)** — required for India retail data under DPDP Act 2023.
- Voice transcripts are stored hashed (SHA-256) for eval purposes; raw audio is **not retained** beyond the 5-second transcription window.
- Customer PII (phone, name, GSTIN) only stored if the owner explicitly tags a credit sale or a B2B invoice. Walk-in cash sales are anonymous by default.
- Owner can export everything as CSV and request deletion within 30 days (DPDP "right to erasure").
