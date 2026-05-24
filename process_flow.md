# Process Flow — Before vs After

## Current State: A typical day at a kirana store

```mermaid
flowchart TD
    Start([Morning: Owner opens shop]) --> Check[Mentally check what's low<br/>by glancing at shelves]
    Check --> Customer{Customer arrives}
    Customer --> Sell[Pick item, quote price from memory]
    Sell --> Pay{Payment mode?}
    Pay -->|Cash| Cash[Take cash, drop in drawer]
    Pay -->|UPI| UPI[Scan QR, verify ping]
    Pay -->|Credit| Khata[Open kachcha bahi<br/>write name + amount]
    Cash --> Note[Maybe scribble in notebook<br/>often forgets]
    UPI --> Note
    Khata --> Next
    Note --> Next{More customers?}
    Next -->|Yes| Customer
    Next -->|No, evening| Reconcile[End of day: try to recall sales<br/>compare cash drawer to memory]
    Reconcile --> Order[Call supplier<br/>'kya kya bhejna hai?']
    Order --> Guess[Guess quantities<br/>often overshoots or stocks out]
    Guess --> CA[Month-end: send WhatsApp photos<br/>of notebook to CA]
    CA --> Pain((Common pains:<br/>stockouts, dead stock,<br/>lost credit, missed GST))

    classDef pain fill:#FEE2E2,stroke:#DC2626,color:#000
    classDef manual fill:#FEF3C7,stroke:#D97706,color:#000
    class Pain pain
    class Check,Note,Khata,Guess,CA manual
```

**Average failure surface:** ~12 manual handoffs per customer-day, each with a forgetfulness/error rate of 5-15%.

---

## Future State: Same day with DukaanAI

```mermaid
flowchart TD
    Start([Morning: Owner opens shop]) --> Brief["DukaanAI sends morning brief:<br/>'3 items low, ₹4,800 expected sales today,<br/>Eid in 5 days — sugar demand +20%'"]
    Brief --> Customer{Customer arrives}
    Customer --> Speak["Owner speaks naturally:<br/>'Do kilo sugar, ek tel,<br/>Raju ke khate mein daal'"]
    Speak --> Parse[Voice Parser → structured action]
    Parse --> Confirm{Trust level<br/>+ confidence?}
    Confirm -->|High conf, L2+| Auto[Auto-log sale + credit entry<br/>show toast: 'logged ₹247']
    Confirm -->|Low conf or new| Verify[UI shows parsed result<br/>owner taps ✅ or corrects]
    Verify --> Auto
    Auto --> Next{More customers?}
    Next -->|Yes| Customer
    Next -->|No, evening| Forecast[Replenishment Agent:<br/>ranked reorder list w/ confidence]
    Forecast --> Voice2["Owner: 'Anna ko sugar 30 kg<br/>aur Maggi 50 packet bhej do'"]
    Voice2 --> POAgent[Supplier PO Agent →<br/>drafts WhatsApp message]
    POAgent --> Review[Owner reviews → ✅ → sent]
    Review --> Day([Done. Books reconciled.<br/>GST-ready. CA gets clean export.])

    classDef ai fill:#DBEAFE,stroke:#2563EB,color:#000
    classDef owner fill:#FEF3C7,stroke:#D97706,color:#000
    classDef good fill:#D1FAE5,stroke:#059669,color:#000
    class Brief,Parse,Forecast,POAgent ai
    class Speak,Voice2,Verify,Review owner
    class Auto,Day good
```

**New failure surface:** ~3 confirmation taps per customer-day (L2 trust), zero for credit/sales reconciliation. Forgetfulness offloaded to the agent.

---

## Quantitative delta (target by end of pilot)

| Metric | Before | After (target) | Source |
|---|---|---|---|
| Time per sale logged | 30-60s (or never) | < 5s | Internal logs |
| Stockouts per week | 8-12 SKUs | 4-6 SKUs (−50%) | Inventory snapshots |
| Time to draft a PO | 15-30 min | < 2 min | Owner stopwatch study |
| Time to monthly GST close | 4-6 hrs at CA | < 1 hr (clean export) | CA invoice |
| Credit ledger leakage | 5-10% never recovered | < 1% | Outstanding-vs-collected |
