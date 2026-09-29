"""Recommendation narrative composition for EchoMind.

Turns the deterministic StrategyAnalysisResult plus recalled Hindsight
StrategicContext into a causal, human-readable recommendation that answers
"why this, why now, and why this format".

An LLM (OpenAI-compatible) is used ONLY when an API key is configured and the
`openai` package is installed. Otherwise a fully deterministic template
narrative is produced so the prototype runs offline with no external calls.
The LLM path degrades to the deterministic path on any error; it never crashes
the recommendation flow.
"""

from typing import Any, Dict, List, Optional

from config.settings import settings

# StrategicContext is only needed for typing; import defensively so this module
# stays importable even if the memory package changes.
try:  # pragma: no cover - defensive import
    from memory.base import InferredMemory, StrategicContext
except Exception:  # pragma: no cover
    InferredMemory = Any  # type: ignore
    StrategicContext = Any  # type: ignore


def compose_recommendation(
    brand: Dict[str, Any],
    analysis: Any,
    context: Optional[Any] = None,
) -> Dict[str, Any]:
    """Compose a recommendation narrative.

    Returns a dict:
        {
            "headline": str,
            "body": str,          # multi-paragraph causal justification
            "source": "llm" | "deterministic",
        }
    """
    deterministic = _compose_deterministic(brand, analysis, context)

    if settings.LLM_API_KEY:
        llm_body = _try_compose_with_llm(brand, analysis, context, deterministic)
        if llm_body:
            return {
                "headline": deterministic["headline"],
                "body": llm_body,
                "source": "llm",
            }

    return deterministic


# ---------------------------------------------------------------------------
# Deterministic (offline) narrative
# ---------------------------------------------------------------------------
def _compose_deterministic(
    brand: Dict[str, Any],
    analysis: Any,
    context: Optional[Any],
) -> Dict[str, Any]:
    pillar = analysis.recommended_pillar or {}
    fmt = analysis.recommended_format or {}

    pillar_name = pillar.get("pillar_name", "an under-served pillar")
    fmt_name = fmt.get("format_name", "your top-performing format")

    headline = f"Publish a '{fmt_name}' post under '{pillar_name}'"

    # WHY THIS (the gap)
    why_this_lines: List[str] = []
    if pillar:
        delta = pillar.get("share_delta_pct")
        actual = pillar.get("actual_share_pct")
        target = pillar.get("target_share_pct")
        days = pillar.get("days_since_last_post")
        gap_bits = []
        if delta is not None and delta < 0:
            gap_bits.append(
                f"it is running {abs(delta)}% below its {target}% target allocation "
                f"(currently {actual}% of output)"
            )
        if isinstance(days, int) and days >= 21:
            gap_bits.append(f"the last post was {days} days ago")
        if gap_bits:
            why_this_lines.append(
                f"Why this pillar: '{pillar_name}' is the largest strategic gap. "
                + "; ".join(gap_bits)
                + "."
            )
        else:
            why_this_lines.append(
                f"Why this pillar: '{pillar_name}' is the best-balanced next move given current cadence."
            )

    # WHY NOW (saturation pressure elsewhere)
    why_now_lines: List[str] = []
    if analysis.saturated_pillars:
        sat = analysis.saturated_pillars[0]
        why_now_lines.append(
            f"Why now: output is over-indexed on '{sat.get('pillar_name')}' "
            f"({sat.get('share_delta_pct'):+}% vs target), so rebalancing now prevents audience fatigue "
            f"and restores topical breadth."
        )
    else:
        why_now_lines.append(
            "Why now: publishing into the gap now keeps the content mix aligned with the target allocation."
        )

    # WHY THIS FORMAT (performance evidence)
    why_format_lines: List[str] = []
    if fmt:
        why_format_lines.append(
            f"Why this format: '{fmt_name}' is the strongest performer at "
            f"{fmt.get('avg_engagement_rate')}% average engagement and "
            f"{fmt.get('avg_clicks')} average clicks."
        )
    if analysis.top_posts:
        top = analysis.top_posts[0]
        why_format_lines.append(
            f"Benchmark: '{top.get('title')}' ({top.get('format_name')}) reached "
            f"{top.get('engagement_rate')}% engagement, a proven template to emulate."
        )

    # Memory-derived context (causal provenance from Hindsight)
    memory_lines = _memory_narrative_lines(context)

    paragraphs: List[str] = []
    paragraphs.append(" ".join(why_this_lines) if why_this_lines else "")
    paragraphs.append(" ".join(why_now_lines))
    paragraphs.append(" ".join(why_format_lines))
    if memory_lines:
        paragraphs.append(" ".join(memory_lines))

    body = "\n\n".join(p for p in paragraphs if p.strip())

    return {"headline": headline, "body": body, "source": "deterministic"}


def _memory_narrative_lines(context: Optional[Any]) -> List[str]:
    if not context:
        return []
    lines: List[str] = []

    constraints = getattr(context, "brand_constraints", None) or []
    if constraints:
        lines.append(
            "Brand guardrails in effect: " + "; ".join(str(c) for c in constraints[:3]) + "."
        )

    beliefs = getattr(context, "active_beliefs", None) or []
    if beliefs:
        top = beliefs[0]
        what = getattr(top, "what_was_learned", None)
        conf = getattr(top, "confidence_score", None)
        if what is not None:
            conf_txt = f" (confidence {conf})" if conf is not None else ""
            lines.append(f"Active belief applied: {what}{conf_txt}.")

    experiences = getattr(context, "relevant_experiences", None) or []
    if experiences:
        lines.append("Prior feedback considered: " + str(experiences[0]))

    return lines


# ---------------------------------------------------------------------------
# Optional LLM narrative
# ---------------------------------------------------------------------------
def _get_openai_client():
    """Build an OpenAI or AzureOpenAI client based on configured settings."""
    import os
    base_url = (settings.LLM_BASE_URL or "").strip()
    api_key = settings.LLM_API_KEY

    # Optional Azure OpenAI support via LLM_BASE_URL or provider='azure'
    if "azure.com" in base_url.lower() or (settings.LLM_PROVIDER or "").lower() == "azure":
        from openai import AzureOpenAI
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
        return AzureOpenAI(
            azure_endpoint=base_url,
            api_key=api_key,
            api_version=api_version,
        )

    from openai import OpenAI
    client_kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def _try_compose_with_llm(
    brand: Dict[str, Any],
    analysis: Any,
    context: Optional[Any],
    deterministic: Dict[str, Any],
) -> Optional[str]:
    """Return an LLM-authored body, or None to fall back deterministically."""
    try:  # pragma: no cover - network / optional dependency path
        client = _get_openai_client()

        system = (
            "You are EchoMind, an AI content strategist. Using ONLY the supplied "
            "evidence, write a concise, high-conviction recommendation that explains "
            "why this pillar, why now, and why this format. Respect all brand "
            "guardrails. Do not invent metrics."
        )
        user = _build_llm_prompt(brand, analysis, context)

        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or None
    except Exception:
        # Any failure (missing package, network, auth) -> deterministic fallback.
        return None


def _build_llm_prompt(
    brand: Dict[str, Any],
    analysis: Any,
    context: Optional[Any],
) -> str:
    lines: List[str] = []
    lines.append(f"BRAND: {brand.get('name')} ({brand.get('industry', 'n/a')})")
    lines.append("")
    lines.append("DETERMINISTIC STRATEGY EVIDENCE:")
    for bullet in analysis.summary_bullets:
        lines.append(f"- {bullet}")
    lines.append("")
    if analysis.recommended_pillar:
        lines.append(f"RECOMMENDED PILLAR: {analysis.recommended_pillar.get('pillar_name')}")
    if analysis.recommended_format:
        lines.append(f"RECOMMENDED FORMAT: {analysis.recommended_format.get('format_name')}")

    if context:
        constraints = getattr(context, "brand_constraints", None) or []
        beliefs = getattr(context, "active_beliefs", None) or []
        experiences = getattr(context, "relevant_experiences", None) or []
        if constraints:
            lines.append("")
            lines.append("BRAND GUARDRAILS (must respect):")
            lines.extend(f"- {c}" for c in constraints)
        if beliefs:
            lines.append("")
            lines.append("ACTIVE STRATEGIC BELIEFS:")
            for b in beliefs:
                what = getattr(b, "what_was_learned", str(b))
                conf = getattr(b, "confidence_score", None)
                lines.append(f"- {what} (confidence {conf})")
        if experiences:
            lines.append("")
            lines.append("RELEVANT PAST FEEDBACK:")
            lines.extend(f"- {e}" for e in experiences)

    lines.append("")
    lines.append("Write 2-3 short paragraphs. Be specific and cite the evidence above.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Post draft generation (turns an accepted recommendation into a deliverable)
# ---------------------------------------------------------------------------
def compose_draft(
    brand: Dict[str, Any],
    recommendation: Dict[str, Any],
    context: Optional[Any] = None,
) -> Dict[str, Any]:
    """Draft the actual post copy for an accepted recommendation.

    Uses the LLM when configured (respecting recalled brand voice/guardrails),
    otherwise returns a structured deterministic outline. Returns
    {"body": str, "source": "llm"|"deterministic"}.
    """
    pillar = (recommendation.get("recommended_pillar") or {}).get("pillar_name", "the target pillar")
    fmt = (recommendation.get("recommended_format") or {}).get("format_name", "the top format")

    if settings.LLM_API_KEY:
        body = _try_compose_draft_with_llm(brand, recommendation, context, pillar, fmt)
        if body:
            return {"body": body, "source": "llm"}

    # Deterministic fallback outline.
    lines = [
        f"**Working title:** {pillar} as a {fmt}",
        "",
        "**Hook:** Lead with a concrete, specific moment (an incident, a metric, a decision).",
        "**Body:** 3–5 beats that teach one idea; show evidence, not opinion.",
        "**Takeaway:** One reusable principle the reader can apply today.",
        "**CTA:** Invite a specific reply (a question, not 'thoughts?').",
    ]
    constraints = list(getattr(context, "brand_constraints", []) or [])
    if constraints:
        lines += ["", "**Voice guardrails applied:**"] + [f"- {c}" for c in constraints[:3]]
    return {"body": "\n".join(lines), "source": "deterministic"}


def _try_compose_draft_with_llm(brand, recommendation, context, pillar, fmt):
    try:  # pragma: no cover - network path
        client = _get_openai_client()

        constraints = list(getattr(context, "brand_constraints", []) or [])
        beliefs = [getattr(b, "what_was_learned", str(b)) for b in (getattr(context, "active_beliefs", []) or [])]
        experiences = list(getattr(context, "relevant_experiences", []) or [])

        guard = "\n".join(f"- {c}" for c in constraints) or "- (none on record)"
        bel = "\n".join(f"- {b}" for b in beliefs) or "- (none on record)"
        exp = "\n".join(f"- {e}" for e in experiences) or "- (none on record)"

        system = (
            "You are EchoMind, a senior content writer. Draft a ready-to-publish "
            "post that strictly respects the brand voice and guardrails. Match the "
            "requested format. Be concrete and evidence-driven; no hype, no clichés."
        )
        user = (
            f"BRAND: {brand.get('name')} ({brand.get('industry','')})\n"
            f"PILLAR: {pillar}\nFORMAT: {fmt}\n\n"
            f"BRAND GUARDRAILS (must respect):\n{guard}\n\n"
            f"LEARNED BELIEFS:\n{bel}\n\n"
            f"PAST FEEDBACK TO HONOR:\n{exp}\n\n"
            "Write the post now. If it's a carousel/thread, output the slides/tweets "
            "as a numbered list. Keep it tight and publishable."
        )
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.6,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception:
        return None
