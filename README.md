# EchoMind: AI Content Strategy Agent with Hindsight Memory

## 1. Project Purpose

EchoMind is a production-quality **AI Content Strategy Agent** built to solve the fundamental flaw of generative marketing tools: **Strategic Amnesia**.

Current AI content tools function as stateless "content vending machines"—generating isolated copy without understanding what succeeded or failed previously, without remembering brand nuance or user critique, and without evolving their editorial recommendations over time.

EchoMind integrates **Hindsight**—an open-source biomimetic long-term memory engine—as the core strategic cognitive layer. By combining Hindsight's multi-network memory (facts, experiences, observations, and evolving beliefs) with deterministic structured analytics, the agent acts as an autonomous strategic partner that:
- Understands brand identity, audience personas, and strict guardrails.
- Evaluates historical content and engagement metrics to pinpoint gaps and saturation.
- Formulates high-conviction next-content recommendations with full causal justification ("why this, why now, and why this format").
- Learns from explicit user feedback (acceptances, edits, rejections with critique).
- Evolves its strategic hypotheses and confidence over time as evidence accumulates.

---

## 2. Architecture & Operational Flow Overview

The architecture implements a dual-engine paradigm: **Structured Relational Storage** for deterministic, tabular metrics, paired with **Hindsight** for qualitative, episodic, and strategic reasoning.

### The Core Operational Loop

```
User Request
     │
     ▼
[ agent/ ] (Orchestrator receives request and sets context)
     │
     ▼
[ memory/ ] (Hindsight Recall: World Facts, Agent Experiences, Evolving Beliefs)
     │
     ▼
[ database/ ] (Structured Query: Content cadence, pillar frequencies, CTR benchmarks)
     │
     ▼
[ strategy/ ] (Strategy Analysis: Gap & saturation detection, pattern synthesis)
     │
     ▼
[ agent/ ] (Recommendation Formulation: Next post concept + causal justification)
     │
     ▼
[ ui/ ] (User Presentation & Review: Marketer inspects, accepts, edits, or rejects)
     │
     ▼
User Feedback (Critique, acceptance, or adjustments)
     │
     ▼
[ memory/ ] (Hindsight Retain & Reflect: Record episode, update facts, calibrate belief confidences)
```

---

## 3. Directory Responsibilities

The codebase enforces strict separation of concerns across seven primary modules:

| Directory | Core Responsibility | Planned Contents |
| :--- | :--- | :--- |
| `agent/` | **Agent Orchestration & Reasoning** | Coordinates the full decision cycle, builds structured prompts, manages LLM communication, and ensures causal provenance in recommendations. |
| `database/` | **Structured Data Persistence** | Manages the relational database (e.g., SQLite / PostgreSQL), SQLAlchemy models, schema migrations, and deterministic analytical queries for posts, channels, and metrics. |
| `memory/` | **Long-Term Strategic Memory (Hindsight)** | Houses the Hindsight memory client integration, abstracting memory operations (`retain`, `recall`, `reflect`) and managing schemas across Hindsight's 4 logical networks. |
| `strategy/` | **Strategy Analytics & Gap Analysis** | Implements domain logic for content auditing: calculating publishing cadences, identifying under-served content pillars, and detecting strategic drift. |
| `ui/` | **User Interface (Streamlit)** | Presentation layer rendering the strategy dashboard, recommendation cards with causal audit sheets, and interactive feedback controls. |
| `tests/` | **Test Suite** | Unit, integration, and behavioral tests validating memory recall, feedback retention, database aggregations, and strategy scoring. |
| `config/` | **Configuration & Environment Settings** | Application settings, environment variable loaders, LLM model parameters, thresholds, and memory bank identifiers. |

---

## 4. Distinction: Structured Data vs. Long-Term Memory

A key design principle of EchoMind is maintaining a sharp boundary between **factual/quantitative data** and **qualitative/strategic memory**:

```
┌───────────────────────────────────────┐   ┌───────────────────────────────────────┐
│     Structured Relational Storage     │   │      Hindsight Long-Term Memory       │
│         (SQLite / PostgreSQL)         │   │        (Biomimetic Memory Bank)       │
├───────────────────────────────────────┤   ├───────────────────────────────────────┤
│ • Exact post copy, timestamps, URLs   │   │ • World Facts: Brand voice, ICP,      │
│ • Channel definitions & format tags   │   │   competitor guardrails, taboos       │
│ • Quantitative metrics (impressions,  │   │ • Agent Experiences: Episodic history │
│   clicks, CTR, likes, shares)         │   │   of recommendations & user critiques │
│ • Factual interaction logs            │   │ • Entity Summaries: Synthesized       │
│   (timestamp, recommendation_id,      │   │   observations on pillars & formats   │
│   decision: ACCEPT / REJECT / EDIT)   │   │ • Evolving Beliefs: Editorial rules   │
│ • Pillar cadence & calendar schedules │   │   of thumb with confidence scores     │
├───────────────────────────────────────┤   ├───────────────────────────────────────┤
│ Role: Deterministic aggregation,      │   │ Role: Causal reasoning, contextual    │
│ exact filtering, and math computation │   │ understanding, and strategy evolution │
└───────────────────────────────────────┘   └───────────────────────────────────────┘
```

### Why Both Are Essential:
- **Relational SQL** answers: *"What was the average engagement rate for carousels vs. text posts in the last 60 days?"* and *"How many days has it been since we published under the 'System Design' pillar?"*
- **Hindsight Memory** answers: *"Why does our audience reject beginner tutorials?"*, *"What editorial angle did the founder approve last month?"*, and *"How confident are we that technical teardowns drive enterprise buyer conversions?"*

---

## 5. Planned Hindsight Integration

EchoMind treats Hindsight as a first-class cognitive substrate rather than an auxiliary search index:

1. **Four Logical Networks:**
   - **World Facts:** Ground truth regarding the brand, ICP constraints, and hard prohibitions (e.g., *"Never disparage competitors"*).
   - **Agent Experiences:** Episodic records of what the agent suggested, how the user responded, and why.
   - **Entity Summaries:** Synthesized behavioral profiles of specific entities (e.g., how the LinkedIn channel behaves differently from Substack).
   - **Evolving Beliefs:** Strategic hypotheses paired with confidence scores (e.g., *"Belief: Technical architecture post-mortems drive 3x more shares than general opinion pieces (Confidence: 0.88)"*).

2. **Core Operations:**
   - **Recall:** Uses multi-strategy retrieval (TEMPR: temporal, entity/graph, keyword matching, and semantic similarity) to gather relevant brand constraints and active beliefs before generating a recommendation.
   - **Retain:** Ingests user decisions (acceptances, edits, critiques) into episodic memory and updates factual brand guidelines.
   - **Reflect:** Synthesizes patterns across recent interactions, updating belief confidences and detecting when brand strategy has drifted.

3. **API-Agnostic Abstraction:**
   The `memory/` package will use an abstract interface (`MemoryClient`) to encapsulate Hindsight calls. This guarantees that application logic remains decoupled from specific SDK method signatures and facilitates seamless testing and local resilience.
