# PRD: DukaanAI — Voice-First Operations Assistant for Retail Chains

**Author:** Kailash | **Version:** 1.0 | **Status:** MVP Specification | **Date:** May 2026

---

## 1. The One-Line

A voice-first conversational AI that store owners *talk to* like a colleague — handling inventory, invoicing, replenishment, and supplier orders — designed for owners who will never learn another app.

---

## 2. The Reframe (Why This Is Different)

Every existing solution in this space — Khatabook, Vyapar, BharatPe, Pine Labs — treats *"owners are not tech-savvy"* as a **bug to fix with better onboarding**. They build form-based UIs and then spend marketing budget convincing owners to adopt them. Adoption stays under 30% for daily active use.

We treat **non-adoption as a design constraint, not a failure mode.** The owner already uses voice all day — with customers, suppliers, family, staff. The interface is already mastered. We just need to be on the other end of that conversation.

This single reframe drives every downstream decision: no forms as primary input, no menu navigation, no "settings" the owner must configure, no onboarding flow. Just a phone number or a chat — and a colleague who knows the store.

---

## 3. Current-State Process Analysis

### 3.1 The "Day in the Life" of a Store Owner

| Time | Activity | Tools Today | Friction |
|---|---|---|---|
| 7:00 AM | Open store, eyeball stock | Eyes, memory | No data — relies on intuition |
| 8:00–11:00 | Serve customers, manual billing | Calculator, kaccha bill book | Slow, GST errors, no record |
| 11:00 | Supplier rep arrives, places order | Verbal, sometimes notebook | Over/under-ordering, no forecast |
| 1:00 PM | Lunch break, ad-hoc stock check | Eyes on shelves | Stockouts already happening |
| 3:00–8:00 | More billing, more stock movement | Same | Compounding data loss |
| 9:00 PM | Day-end: count cash, estimate sales | Memory, cash drawer | No actual reconciliation |
| Weekly | Place orders with 6–10 suppliers | Phone calls | Reactive, panic ordering |
| Monthly | GST filing (often delegated, often late) | CA, paper bills | Penalties, compliance debt |

### 3.2 Five Critical Pain Points (with Root Causes)

| # | Pain Point | Root Cause | Business Impact |
|---|---|---|---|
| **P1** | **Inventory mismatches** between system and shelf | Data entry depends on the owner remembering to update — and they don't | 8–15% stock variance; dead stock and phantom inventory |
| **P2** | **Frequent stockouts** on fast-movers, esp. before festivals/weekends | Replenishment is reactive (notice empty → reorder), not predictive | Lost sales (~12% revenue leakage), customer churn to competing kirana |
| **P3** | **Manual invoicing delays + GST non-compliance** | Owner won't pause a sale to fill a digital form — bill is written on paper, never digitized | GST input credit lost, ITR-4 filing nightmares, audit risk |
| **P4** | **Over/under-ordering with suppliers** | No demand forecast; orders are placed on supplier-rep schedule, not stock-need | Working capital tied in dead stock OR cash lost to emergency wholesaler markup |
| **P5** | **Tech adoption barrier** — existing apps abandoned within 2 weeks | Apps demand the owner change behavior; the owner is busy serving 200 customers/day | All upstream investments in digital tools fail to compound; data stays in silos |

### 3.3 Why "Just Build a Better App" Doesn't Work

The retail tech graveyard is full of apps with great UX that 80% of owners abandoned. The constraint isn't UX polish — it's **cognitive switching cost** during a 12-hour shift. Anything that asks the owner to *stop serving a customer and tap through screens* loses to "I'll do it later" — and "later" never comes.

---

## 4. Requirement Gathering Plan

| Phase | Activity | Participants | Output | Duration |
|---|---|---|---|---|
| **R1 — Discovery** | Shadow 6 stores across 3 city tiers (metro, tier-2, tier-3) for 2 days each | UX researcher + PM | "Day in life" video diaries, friction log | 2 weeks |
| **R2 — Voice corpus** | Record 200+ hours of natural owner-supplier-customer conversations (with consent) | Linguist + field team | Multilingual corpus for prompt tuning (Tamil/Hindi/Hinglish/Tanglish) | 3 weeks |
| **R3 — Quantitative baseline** | Audit POS data from 20 willing stores: stockout frequency, invoice latency, order cycle | Data analyst | Baseline KPI numbers | 2 weeks |
| **R4 — Supplier landscape** | Interview top 30 FMCG/grocery distributors on integration appetite, EDI capability | BD + PM | Supplier readiness matrix | 2 weeks |
| **R5 — Regulatory** | Review GST e-invoicing thresholds, FSSAI, state-level retail rules | Compliance counsel | Compliance map | 1 week |
| **R6 — Co-design workshops** | 3 sessions × 8 owners each — paper prototype to voice-script roleplay | UX + PM | Validated conversation flows | 2 weeks |
| **R7 — Pilot cohort sign-up** | Recruit 10 stores willing to pilot for 8 weeks | BD | Signed pilot agreements | Parallel |

Total: ~12 weeks of structured discovery before code freeze on MVP scope.

**Critical method note:** No surveys. Owners are gracious to surveys and lie to be polite. Observation, voice corpus, and POS data tell the truth.

---

## 5. Solution Blueprint

### 5.1 System Architecture (high-level)

```
┌──────────────────────────────────────────────────────────────────┐
│                       OWNER TOUCHPOINTS                          │
│   WhatsApp Voice  │  Phone Call  │  Web Chat  │  In-Store Tablet │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   SPEECH-TO-TEXT GATEWAY     │
            │  (multilingual: ta/hi/en)    │
            └──────────────┬───────────────┘
                           ▼
            ┌──────────────────────────────┐
            │    CONVERSATIONAL ROUTER     │ ◄── classifies intent
            │     (Claude — orchestrator)  │
            └──┬────┬─────┬─────┬──────────┘
               │    │     │     │
       ┌───────┘    │     │     └────────────┐
       ▼            ▼     ▼                  ▼
  ┌─────────┐ ┌────────┐ ┌─────────┐  ┌──────────────┐
  │ Voice   │ │Invoice │ │Replenish│  │  Supplier    │
  │ Parser  │ │ Agent  │ │ Forecast│  │  PO Agent    │
  │ Agent   │ │        │ │  Agent  │  │              │
  └────┬────┘ └───┬────┘ └────┬────┘  └──────┬───────┘
       │          │           │              │
       └──────────┴───────────┴──────────────┘
                       │
                       ▼
            ┌──────────────────────────────┐
            │      STATE LAYER             │
            │ Inventory │ Sales │ Suppliers│
            │  (Postgres + Redis cache)    │
            └──────────────┬───────────────┘
                           ▼
            ┌──────────────────────────────┐
            │    INTEGRATIONS              │
            │ GST e-Invoice │ Tally │ POS  │
            │ Distributor APIs │ WhatsApp  │
            └──────────────────────────────┘
```

### 5.2 The Five Agents (Specialist Multi-Agent Design)

| Agent | Job-To-Be-Done | Input | Output |
|---|---|---|---|
| **Voice Parser Agent** | Convert messy code-mixed speech into structured action JSON | Raw transcript + store context | `{action, sku_matches[], quantities[], confidence, clarification_needed}` |
| **Invoice Agent** | Generate GST-compliant invoice from conversational ask | Customer ref, line items, payment mode | Invoice JSON + WhatsApp-ready PDF |
| **Replenishment Forecast Agent** | Predict 7-day depletion per SKU + auto-draft POs | Sales history, current stock, calendar context (festivals, weather, day-of-week) | Ranked replenishment list with confidence + reasoning |
| **Supplier PO Agent** | Match owner's verbal order to supplier catalogs, draft PO | "Order from Patanjali rep" + last 30d sales | Draft PO + delivery ETA |
| **Conversational Router** | Orchestrator — classifies intent, routes, asks clarifying questions, maintains memory | Full conversation history | Tool calls + natural-language reply |

### 5.3 The "Trust Ladder" — Why We Don't Auto-Execute

A critical design choice that separates this from naive automation:

```
Level 1 (Week 1–2):  AI suggests → Owner approves every action
Level 2 (Week 3–8):  AI auto-executes low-risk (sales logging),
                     suggests high-risk (POs > ₹10k)
Level 3 (Month 3+):  AI auto-executes most actions, owner reviews daily digest
```

Owners do not trust automation that takes actions they didn't see. The ladder builds trust before it asks for it. This is the lesson every B2C agentic product learns the hard way.

---

## 6. Data Utilization Approach

### 6.1 What Data Flows Where

| Data Source | Purpose | Storage | Retention |
|---|---|---|---|
| Voice transcripts | Real-time action parsing + corpus for prompt tuning | Encrypted blob; transcripts redacted of PII | 90 days hot, anonymized 2 years |
| Sales transactions | Demand forecasting, customer LTV | Postgres | Indefinite (with owner consent) |
| Stock movements | Inventory variance detection | Postgres + Redis cache | Indefinite |
| Supplier catalogs | SKU matching, price benchmarking | Postgres | Refresh weekly |
| Calendar/weather/festival | Forecast covariates | External APIs cached daily | 7-day cache |
| Owner-AI conversations | Conversation memory + model improvement | Vector DB (Pinecone) | 30 days per session |

### 6.2 The Three Data Loops

1. **Operational loop** (real-time): Voice → action → inventory state → confirmation back to owner. **Latency target: <3 seconds end-to-end.**
2. **Analytical loop** (overnight): Aggregate sales → retrain depletion forecasts per SKU per store. Backtested forecasts displayed alongside predictions for explainability.
3. **Learning loop** (weekly): Anonymized voice corpora + correction signals (when owner overrides AI suggestion) → prompt fine-tuning + few-shot example refresh.

### 6.3 Privacy and Consent

- Owner data is owner-owned; export-on-demand by default.
- Customer PII (names, phone) is hashed for analytics; raw only for the owner's own invoicing.
- No cross-store data sharing without explicit opt-in (benchmarking is opt-in).
- Voice transcripts are processed in-region (Mumbai DC for India) to align with DPDP Act 2023.

---

## 7. KPIs (5)

| # | KPI | Definition | MVP Target | North-Star Tie |
|---|---|---|---|---|
| **K1** | **Voice Intent Accuracy** | % of voice commands correctly parsed without clarification | ≥ 90% | Trust ladder progression |
| **K2** | **Stockout Reduction** | Stockout-days per SKU vs. pre-DukaanAI baseline | -50% within 90 days | Revenue recovery |
| **K3** | **Time-to-Invoice** | Median seconds from sale completion to GST-compliant invoice issued | < 30 seconds | Compliance + customer experience |
| **K4** | **PO Acceptance Rate** | % of AI-drafted POs the owner sends with ≤ 1 edit | ≥ 75% | Working capital optimization |
| **K5** | **Daily Active Owners** | % of pilot store owners using DukaanAI ≥ 5 days/week | ≥ 80% by week 8 | Adoption — the real moat |

**Why these five:** They map 1:1 to the five pain points. K5 is the leading indicator everything else depends on — if owners aren't talking to it daily, nothing downstream matters.

---

## 8. Risk Considerations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **R1 — Voice recognition fails on code-mixed Tamil/Hindi/Hinglish** | High | High | Multilingual ASR (Sarvam/Bhashini) + Claude as fallback semantic parser; corpus tuning from R2 above |
| **R2 — Owner doesn't trust AI to log sales accurately** | High | High | Trust ladder (Section 5.3); read-back confirmations in Level 1; visible undo |
| **R3 — Supplier integration fails (no APIs)** | High | Medium | WhatsApp PDF PO fallback; manual delivery confirmation via voice |
| **R4 — GST e-invoicing rule changes** | Medium | High | Compliance counsel on retainer; invoicing module isolated for fast updates |
| **R5 — Forecast wrong → owner over-orders → cash crunch** | Medium | High | Confidence bands shown to owner; never auto-execute POs above ₹X threshold in Level 1–2 |
| **R6 — LLM hallucinates inventory action (e.g., wrong SKU debited)** | Medium | High | Structured output enforcement (Pydantic); SKU match confidence threshold ≥ 0.85 else clarify; daily variance reconciliation |
| **R7 — Owner data privacy breach** | Low | Severe | In-region processing; SOC 2 from day 1; data export & delete on demand |
| **R8 — Cannibalization fear from suppliers (transparency = pricing pressure)** | Medium | Medium | Position as partner tool, not marketplace; suppliers see their share of business grow with better forecasting |
| **R9 — Unit economics break at scale (LLM cost per voice command)** | Medium | Medium | Aggressive caching, smaller models for routing, Claude only for ambiguous parses |

---

## 9. MVP Scope (8-Week Pilot)

**In scope:**
- Voice Parser Agent (Tamil/Hindi/English code-mixed)
- Inventory state + sales logging via voice
- Invoice Agent (GST-compliant PDF via WhatsApp)
- Replenishment Forecast Agent (suggestions only, no auto-execute)
- Web/WhatsApp chat interface
- 10-store pilot, 1 city, 1 vertical (kirana)

**Out of scope (Phase 2):**
- Direct supplier API integration (use WhatsApp PDF fallback)
- Multi-store dashboards for chain operators
- Loyalty/customer features
- Lending integrations
- Phone-call voice (calls are batched/delayed; WhatsApp voice is real-time enough)

**Success criteria for graduating MVP:**
- 8 of 10 pilot stores hit K5 ≥ 80% DAU
- K1 (intent accuracy) ≥ 90% on production traffic
- Net Promoter from store owners ≥ 50

---

## 10. Open Questions

1. Phone-call interface — Phase 2 or core? Hinges on WhatsApp voice adoption in pilot.
2. Should we white-label this for FMCG distributors (Patanjali, Dabur) as the GTM wedge, or go direct to stores?
3. How do we handle the multi-owner store (family-run, 3 people input commands) — single voice model or speaker-diarized?
4. Pricing model: per-store subscription vs. per-transaction vs. supplier-side revenue share?
5. Does the trust ladder progression auto-advance, or does the owner explicitly choose to grant more autonomy?

---

## 11. Appendix: Why I Believe This Will Work

The wedge is not "AI for retail." The wedge is **"the only retail tool that doesn't ask you to change."** Every other product treats the owner as the problem. We treat the owner as the user, and the *interface* as the problem to solve.

If we are right, K5 (daily active owners) will be 3–5× what Khatabook achieved, because we are not competing with their UX — we are competing with paper and memory, which is what owners actually use today.
