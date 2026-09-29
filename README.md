# EchoMind: AI Content Strategy Agent with Hindsight Memory

**EchoMind cures "strategic amnesia."** Most AI content tools are stateless vending machines. They generate copy but never remember what worked, what the brand's voice is, or what you rejected last week. EchoMind pairs **deterministic analytics** (SQLite) with **[Hindsight](https://hindsight.vectorize.io/) long-term memory** so the agent learns from every decision and gets measurably better over time.

> Deterministic math decides **which** editorial pillar is under-served. Hindsight memory decides **how** to win it: the angle, the format, and the brand voice, learned from real feedback.

---

## Why it matters

Marketing teams constantly reinvent the wheel. EchoMind remembers:
- **What performed:** quantitative metrics per pillar, format, and post.
- **What the brand is:** voice, audience (ICP), and hard guardrails ("never post beginner tutorials").
- **What you decided:** every accept, edit, or reject with critique.
- **What it has learned:** evolving beliefs consolidated from evidence.

The result is a recommendation with full causal justification ("why this, why now, why this format") that **improves with each interaction**.

---

## The "memory is the star" moment

The app shows the same analysis narrated twice:

| Without memory (stateless) | With Hindsight memory |
| :--- | :--- |
| Generic pick, generic prose | On-brand voice, learned angle |
| No history | Recalls past rejections and critiques |
| Fixed format | **Switches format** when past feedback rejected the default |
| Flat confidence | **Conviction rises** as evidence accumulates |

The **Learning** page runs a full cycle in one click (recommend, reject with critique, recommend again) and highlights the exact structural diff (format, angle, conviction) caused by memory.

---

## Architecture & Multipage Navigation

```
User
  │
  ▼
ui/app.py (Streamlit Multipage Navigation via st.navigation & st.Page)
  │
  ├──► ui/pages/overview.py     [Factual KPIs, pillar distribution vs targets, format benchmarks]
  ├──► ui/pages/strategy.py     [Next recommendation, decision provenance, guardrail audit, weekly plan]
  ├──► ui/pages/learning.py     [Interactive accept/edit/reject feedback loop & before/after diff]
  ├──► ui/pages/memory.py       [Memory bank inspector, belief conviction timeline, evidence links]
  ├──► ui/pages/ask.py          [Conversational strategist Q&A via Hindsight reflection]
  └──► ui/pages/system.py       [Runtime diagnostics, model configuration, architecture briefing]
  │
  ▼
agent/orchestrator.py ──► strategy/engine.py ──► database/ (SQLite)   [WHAT is under-served: deterministic gap math]
  │
  ├──► memory/ (Hindsight)            [WHY / HOW: brand voice, past feedback, evolving beliefs]
  │        recall -> beliefs, facts, experiences
  │
  ├──► agent/llm.py (Groq / Azure OpenAI) [narrative + on-brand draft, with deterministic fallback]
  ├──► agent/guardrails.py            [Responsible AI: automated compliance verification against brand rules]
  └──► strategy/calendar.py           [Weekly editorial plan generation, exportable to Markdown and CSV]
```

| Module | Responsibility |
| :--- | :--- |
| `agent/` | Orchestration, memory-informed planning, decision provenance, guardrails, LLM narrative and draft generation |
| `database/` | SQLite schema, repository, deterministic aggregations, demo seed data |
| `memory/` | Hindsight adapter (plus offline mock) behind a clean `MemoryAdapter` contract |
| `strategy/` | Deterministic gap and saturation detection, weekly editorial calendar export |
| `config/` | Environment and `.env` loading, settings, memory-bank ID derivation |
| `ui/` | Native multipage Streamlit app (`overview`, `strategy`, `learning`, `memory`, `ask`, `system`) with theme-adaptive styling |
| `tests/` | Comprehensive test suite (memory loop, adapters, strategy, guardrails, calendar) |

---

## Key Features

1. **Decision Provenance Matrix:** Every recommendation provides a complete causal audit trail showing every factual metric and recalled memory item (category, evidence, age, influence weight, and decision impact). No black-box outputs.
2. **Responsible AI Guardrail Verification:** Every generated draft is evaluated against active brand rules (voice guidelines, target ICP, taboo rules) and displays an automated pass/fail compliance matrix with reasons.
3. **Exportable Weekly Editorial Calendar:** Converts detected strategic deficits into a balanced 5-day editorial plan exportable directly as **CSV** and **Markdown**.
4. **Honest Uncertainty:** Clearly identifies low-evidence recommendations as *Exploratory* and displays an explicit assumptions callout when historical volume or feedback is sparse.
5. **Belief Conviction Timeline:** Visualizes how the agent's confidence in strategic beliefs strengthens over time as supporting evidence accumulates.
6. **Restrained Visual Design:** Native Light, Dark, and System default mode support using theme variables and WCAG AA compliant design tokens. No emojis in headings, no neon glows, and no marketing fluff.

---

## How Hindsight memory is used

EchoMind treats Hindsight as its cognitive layer, not a search index. See `memory/hindsight_adapter.py`.

- **One memory bank per brand** (`ensure_bank`) with a strategist **mission** and **disposition**, giving strict tenant isolation and a consistent reasoning personality.
- **Retain** (`retain_*`): brand rules are stored as **world facts**; every accept, edit, or reject with critique is stored as an **experience** (with structured metadata). Retain is synchronous so the fact is immediately recallable.
- **Recall** (`recall_strategic_context`): three type-scoped recalls (`types=["world"]`, `["experience"]`, `["observation"]`) using Hindsight's multi-strategy retrieval gather guardrails, past feedback, and learned beliefs before every recommendation.
- **Observations become evolving beliefs**: Hindsight automatically consolidates repeated evidence into deduplicated, evidence-grounded **observations**. EchoMind surfaces these as the agent's beliefs, so there is no hand-rolled belief store.
- **Reflect** (`reflect_on_strategy`): powers the **Ask the strategist** page and strategy synthesis, shaped by the bank's mission and disposition.
- **Memory changes the decision, not just the words**: recalled rejections switch the recommended format, and recalled beliefs or critiques set the editorial angle (`agent/orchestrator.py::_memory_plan`).

If Hindsight is unreachable, EchoMind degrades **transparently** to deterministic-only and says so. It never silently falls back to the mock.

---

## Quick start

Requires **Python 3.12** (recommended; 3.13 also works). You also need a [Hindsight](https://ui.hindsight.vectorize.io/signup) key (Cloud has free credits) and an LLM key ([Groq](https://console.groq.com/keys) recommended).

**1. Create a virtual environment and install:**

```bash
python -m venv .venv
```
```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```
```bash
# macOS / Linux
source .venv/bin/activate
```
```bash
pip install -r requirements.txt
```

**2. Configure keys** (copy the template, then edit `.env`):

```powershell
Copy-Item .env.example .env      # Windows
```
```bash
cp .env.example .env             # macOS / Linux
```

```ini
HINDSIGHT_API_KEY=your-hindsight-cloud-key

# Option A: Groq (Default)
LLM_PROVIDER=groq
LLM_API_KEY=your-groq-key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b

# Option B: Azure OpenAI (Optional)
# LLM_PROVIDER=azure
# LLM_API_KEY=your-azure-key
# LLM_BASE_URL=https://<your-resource-name>.openai.azure.com/
# LLM_MODEL=<your-deployment-name>
# AZURE_OPENAI_API_VERSION=2024-06-01
```

`.env` is auto-loaded at startup and is gitignored.

**3. Seed the demo database** (two brands):

```bash
python -m database.seed
```

**4. Run:**

```bash
streamlit run ui/app.py
```

**Offline mode:** set `HINDSIGHT_USE_MOCK=true` to run with the in-memory mock and no LLM (deterministic narratives). Useful for development and CI.

---

## Demo flow (75 seconds)

1. **Overview:** Show the *Engineering Culture & Leadership* gap (6.7% actual vs 20% target).
2. **Strategy:** Click *Generate recommendation*. Contrast *Without memory* vs *With Hindsight memory*. Inspect the **Decision Provenance Matrix** and generate a draft to verify **Responsible AI Guardrail Checks**.
3. **Learning:** Run the *Learning simulation*. Show the before/after diff highlighting how the format switched, the angle adapted, and the critique was recalled.
4. **Memory:** Open the memory inspector. View the belief conviction timeline and evidence links. Switch brand to *Verdant Coffee Co.* in the sidebar to prove strict tenant isolation.
5. **Ask:** Ask "What should we avoid, and why?" to show Hindsight reflection synthesizing patterns.
6. **System:** Review the architecture diagram and diagnostics confirming memory backend and model configuration.

---

## Testing

```bash
pytest
```

The suite is hermetic (it forces deterministic narratives and uses an isolated temporary database and the in-memory mock). Tests that require the Hindsight SDK or a live server skip cleanly when unavailable.

---

## Tech stack

Python 3.12+, Streamlit 1.40+, Altair, SQLite, [Hindsight](https://hindsight.vectorize.io/) (`hindsight-client`), and Groq / Azure OpenAI (OpenAI-compatible LLM client).
