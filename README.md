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

The **Watch it learn** tab runs a full cycle in one click (recommend, reject with critique, recommend again) and you can see the recommendation itself change.

---

## Architecture

```
User
  │
  ▼
agent/orchestrator.py ──► strategy/engine.py ──► database/ (SQLite)   [WHAT is under-served: deterministic gap math]
  │
  ├──► memory/ (Hindsight)            [WHY / HOW: brand voice, past feedback, evolving beliefs]
  │        recall -> beliefs, facts, experiences
  │
  ├──► agent/llm.py (Groq)            [narrative + on-brand draft, with deterministic fallback]
  │
  ▼
ui/app.py (Streamlit)                 [Dashboard · Recommendation · Watch it learn · Memory · Ask]
  │
  ▼
Feedback (accept / edit / reject + critique) ──► memory/ retain ──► the loop learns
```

| Module | Responsibility |
| :--- | :--- |
| `agent/` | Orchestration, memory-informed planning, LLM narrative and draft generation |
| `database/` | SQLite schema, repository, deterministic aggregations, demo seed data |
| `memory/` | Hindsight adapter (plus offline mock) behind a clean `MemoryAdapter` contract |
| `strategy/` | Deterministic gap and saturation detection |
| `config/` | Environment and `.env` loading, settings, memory-bank ID derivation |
| `ui/` | Streamlit app (5 tabs, custom theme) |
| `tests/` | `unittest` suite (memory loop, adapters, strategy) |

---

## How Hindsight memory is used

EchoMind treats Hindsight as its cognitive layer, not a search index. See `memory/hindsight_adapter.py`.

- **One memory bank per brand** (`ensure_bank`) with a strategist **mission** and **disposition**, giving strict tenant isolation and a consistent reasoning personality.
- **Retain** (`retain_*`): brand rules are stored as **world facts**; every accept, edit, or reject with critique is stored as an **experience** (with structured metadata). Retain is synchronous so the fact is immediately recallable.
- **Recall** (`recall_strategic_context`): three type-scoped recalls (`types=["world"]`, `["experience"]`, `["observation"]`) using Hindsight's TEMPR multi-strategy retrieval gather guardrails, past feedback, and learned beliefs before every recommendation.
- **Observations become evolving beliefs**: Hindsight automatically consolidates repeated evidence into deduplicated, evidence-grounded **observations**. EchoMind surfaces these as the agent's beliefs, so there is no hand-rolled belief store.
- **Reflect** (`reflect_on_strategy`): powers the **Ask the strategist** tab and strategy synthesis, shaped by the bank's mission and disposition.
- **Memory changes the decision, not just the words**: recalled rejections switch the recommended format, and recalled beliefs or critiques set the editorial angle (`agent/orchestrator.py::_memory_plan`).

If Hindsight is unreachable, EchoMind degrades **transparently** to deterministic-only and says so. It never silently falls back to the mock.

---

## Quick start

Requires **Python 3.12** (recommended; 3.13 also works). Note that Python 3.14 currently lacks prebuilt wheels for some dependencies. You also need a [Hindsight](https://ui.hindsight.vectorize.io/signup) key (Cloud has free credits) and an LLM key ([Groq](https://console.groq.com/keys) recommended).

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

```
HINDSIGHT_API_KEY=your-hindsight-cloud-key
LLM_API_KEY=your-groq-key
# Defaults: Hindsight Cloud + Groq openai/gpt-oss-120b. Override in .env if needed.
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

## Demo flow (60 to 90 seconds)

1. **Dashboard:** point out the *Engineering Culture & Leadership* gap (6.7% actual vs 20% target).
2. **Recommendation:** click *Generate* and compare *Without memory* vs *With Hindsight memory*: on-brand angle, recalled guardrails and beliefs, and a conviction boost.
3. **Watch it learn:** one click rejects a recommendation with a critique and regenerates; the format and angle change and the agent recalls your critique.
4. **Memory:** open the brand's brain (world facts, observations, experiences), then switch to *Verdant Coffee Co.* to prove tenant isolation.
5. **Ask:** ask "What should we avoid, and why?" and get an answer from Hindsight reflection.

---

## Testing

```bash
python -m unittest discover -s tests
```

The suite is hermetic (it forces deterministic narratives and uses a temporary database and the in-memory mock). Tests that require the Hindsight SDK or a live server skip cleanly when unavailable.

---

## Tech stack

Python, Streamlit, SQLite, [Hindsight](https://hindsight.vectorize.io/) (`hindsight-client`), and Groq (OpenAI-compatible LLM API).
