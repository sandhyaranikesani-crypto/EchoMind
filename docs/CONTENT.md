# EchoMind — Content Deliverables (draft)

Personalize the voice and add your own screenshots/links before publishing.

---

## Article (blog / dev.to / Hashnode) — ~600 words

### I built an AI content strategist that actually remembers — here's what changed

Every generative marketing tool I've used has the same fatal flaw: amnesia. It
writes a post, forgets it, and cheerfully suggests the exact idea you killed
last week — in a voice that isn't your brand's. I wanted to fix that, so I built
**EchoMind**: an AI content strategy agent with a real long-term memory.

**The core idea: split "what" from "how."**
EchoMind runs on two engines. A deterministic SQLite layer answers the
*objective* question — which editorial pillar is under-served right now? That's
just math: actual vs target share, days since last post, engagement by format.
The second engine, **[Hindsight](https://hindsight.vectorize.io/)**, answers the
*subjective* one — how do we win this pillar for *this* brand? That's where
memory lives: brand voice, hard guardrails, and every decision the marketer has
ever made.

**Why Hindsight instead of a vector store?**
I didn't want a search index; I wanted an agent that *learns*. Hindsight stores
memories as **world facts** (objective brand rules) and **experiences** (the
agent's own actions and the feedback it got). In the background it consolidates
repeated evidence into **observations** — deduplicated, evidence-grounded
beliefs that get refined, not overwritten, as new evidence arrives. So "carousel
post-mortems out-perform opinion pieces" isn't something I hard-coded; it's a
belief the system forms and grows confidence in.

**The moment that sells it.**
The app renders the same analysis twice: once *without* memory and once *with*.
Without memory it's generic. With memory it recalls the brand's guardrails,
applies a learned angle, and — this is the part I'm proud of — **changes the
actual recommendation**. If past feedback rejected the default format, EchoMind
recalls that experience and switches to the next best performer, and it tells
you exactly why.

There's a one-click "Watch it learn" flow: it makes a recommendation, I reject
it with a critique, and it recommends again — now recalling the critique and
adapting the plan. Confidence rises as evidence accumulates. It feels less like
a tool and more like a strategist who's been on the team for months.

**Engineering notes.**
- Each brand gets its own Hindsight **bank** with a strategist *mission* and
  *disposition*, so memories never leak across tenants and `reflect` reasons in
  a consistent voice.
- Recalls are **type-scoped and run in parallel** for latency.
- The LLM layer (Groq's OpenAI-compatible API) writes the narrative and an
  on-brand draft, with a deterministic fallback so the app still works offline.
- If Hindsight is ever unreachable, the agent degrades transparently to
  deterministic-only — it never pretends to remember.

**What I learned.**
Memory changes the product category. A stateless generator competes on prose; a
memory-backed agent compounds — it's more useful in week 12 than on day one.
That's the difference between a demo and something a team would actually pay
for.

Code + demo: [link]. Built for the Hindsight memory hackathon.

---

## LinkedIn post

Most AI writing tools have amnesia. They'll pitch you the idea you rejected last
week, in a voice that isn't your brand's.

So I built **EchoMind** — an AI content strategist with real long-term memory,
powered by Hindsight.

Two engines:
• Deterministic analytics decide **which** content pillar is under-served (pure
math).
• Hindsight memory decides **how** to win it — brand voice, guardrails, and
every accept/edit/reject you've ever made.

The fun part: it doesn't just reword things. When past feedback rejected a
format, it **recalls that and changes the recommendation** — and its confidence
rises as evidence accumulates. Reject a suggestion with a critique, and the next
one adapts.

Stateless tools compete on prose. A memory-backed agent compounds — more useful
in month 3 than on day 1.

Demo + code 👇 [link]
#AI #Agents #Hindsight #MemoryHackathon #ContentStrategy

---

## X / Twitter post

Built EchoMind: an AI content strategist that *remembers*.

Most tools re-pitch the idea you killed last week. EchoMind uses @vectorize_io
Hindsight to recall your brand voice + every past accept/edit/reject — and
actually changes its recommendation based on what it learned.

Watch it get smarter in one click 👇 [link]
