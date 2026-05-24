# Solution Architecture

## High-level system

```mermaid
graph TB
    subgraph Owner["Store Owner"]
        Mic["🎙️ Voice Input<br/>(Tamil / Hindi / English / mixed)"]
        UI["📱 DukaanAI Chat UI<br/>(WhatsApp / PWA)"]
    end

    subgraph Router["Conversational Router (LLM)"]
        Orchestrator["Orchestrator<br/>+ Trust-Ladder Gate"]
    end

    subgraph Agents["Specialist Agents"]
        VP["🗣️ Voice Parser<br/>transcript → intent JSON"]
        RF["📈 Replenishment Forecast<br/>history + festivals → reorder list"]
        IA["🧾 Invoice Agent<br/>line items → GST invoice"]
        PO["📦 Supplier PO Agent<br/>verbal request → draft PO"]
    end

    subgraph Data["Data Layer"]
        Inv[(Inventory)]
        Sales[(Sales History)]
        Cat[(SKU Catalog)]
        Sup[(Suppliers)]
        Cal[(Festival Calendar)]
    end

    subgraph External["External Systems"]
        WA["WhatsApp Business API"]
        GST["GST e-Invoice Portal"]
        Bank["UPI / Payment Gateways"]
        Tally["Tally / Accountant Export"]
    end

    Mic --> UI
    UI --> Orchestrator
    Orchestrator --> VP
    Orchestrator --> RF
    Orchestrator --> IA
    Orchestrator --> PO

    VP <--> Cat
    RF <--> Sales
    RF <--> Inv
    RF <--> Cal
    IA <--> Cat
    IA <--> Inv
    PO <--> Sup
    PO <--> Cat

    PO --> WA
    IA --> GST
    IA --> Tally
    UI --> Bank

    Orchestrator -.confirm/auto.-> UI

    classDef owner fill:#FFF4E6,stroke:#F59E0B,color:#000
    classDef router fill:#E0F2FE,stroke:#0EA5E9,color:#000
    classDef agent fill:#F0FDF4,stroke:#16A34A,color:#000
    classDef data fill:#F5F3FF,stroke:#7C3AED,color:#000
    classDef ext fill:#FEF2F2,stroke:#DC2626,color:#000
    class Mic,UI owner
    class Orchestrator router
    class VP,RF,IA,PO agent
    class Inv,Sales,Cat,Sup,Cal data
    class WA,GST,Bank,Tally ext
```

## Why a multi-agent design instead of one monolithic prompt

| Concern | Monolithic prompt | Specialist agents |
|---|---|---|
| **Prompt regression risk** | Any tweak risks all flows | Isolated — invoice fix doesn't touch voice parsing |
| **Eval & accuracy tracking** | Single blended metric | Per-agent gold sets + per-agent KPIs (K1 voice-intent, K3 invoice latency) |
| **Latency budget** | One giant context every turn | Router calls only the agents needed; each agent runs with a tight context |
| **Cost** | Pays for max context every call | Cheaper models per agent where appropriate |
| **Team scaling** | One PM owns everything | Agents become product surfaces with clear ownership |

This mirrors the pattern shipped in Feature Gate (Anthropic-internal multi-agent system) and ChatFactory (the agent we shipped at PathFactory) — proven cleaner to operate than monolithic prompts.

## Trust Ladder (autonomy progression)

```mermaid
stateDiagram-v2
    [*] --> L1: New store onboarded
    L1: Level 1 — Apprentice<br/>Every action confirmed before execution
    L2: Level 2 — Familiar<br/>Auto-log sales, confirm POs & invoices
    L3: Level 3 — Trusted<br/>Auto-execute most. Confirm POs > ₹10K only

    L1 --> L2: 100 actions w/ ≥95% acceptance
    L2 --> L3: 500 actions w/ ≥97% acceptance,<br/>zero rollback in last 14d
    L2 --> L1: 3 consecutive rejections → demote
    L3 --> L2: Any rollback or compliance miss → demote
```

Demotion is silent — the owner just sees more confirmations. This is the core mechanism that keeps the system honest with low-trust users.
