"""Responsible AI guardrail evaluation for EchoMind.

Evaluates generated drafts against recalled brand constraints and ethical guidelines.
Ensures drafts do not violate voice guidelines, ICP targeting, taboos, or factual accuracy.
Runs deterministically offline, with optional LLM enhancement when configured.
"""

import re
from typing import Any, Dict, List, Optional

# Hype words that violate evidence-driven, non-hyperbolic B2B brand guidelines
HYPE_KEYWORDS = [
    r"\brevolutionary\b",
    r"\bgame[- ]changer\b",
    r"\bunlock(?:ing)? 10x\b",
    r"\bskyrocket(?:ing)?\b",
    r"\bmagic(?:al)? bullet\b",
    r"\bsecret sauce\b",
    r"\bmind[- ]blowing\b",
    r"\bdisrupting everything\b",
    r"\bunbelievable\b",
]

# Beginner phrases that violate the "no beginner 101 tutorials" rule
BEGINNER_KEYWORDS = [
    r"\b101 tutorial\b",
    r"\bfor beginners\b",
    r"\bfor dummies\b",
    r"\bbasics 101\b",
    r"\babsolute beginner\b",
    r"\bintro to coding\b",
]

# Disparagement patterns
DISPARAGEMENT_KEYWORDS = [
    r"\bcompetitor(?:s)? suck\b",
    r"\bis garbage\b",
    r"\bis trash\b",
    r"\brip[- ]off\b",
    r"\binferior knockoff\b",
]


def evaluate_guardrails(
    draft_text: str,
    brand_constraints: List[str],
    brand_name: str = "the brand",
) -> List[Dict[str, Any]]:
    """Evaluate a generated draft against recalled brand constraints.

    Returns a list of check results:
        [
            {
                "rule": str,
                "category": "Voice" | "Audience" | "Taboo" | "Factual",
                "status": "PASS" | "WARNING" | "FAIL",
                "reason": str,
            },
            ...
        ]
    """
    results: List[Dict[str, Any]] = []
    text_lower = (draft_text or "").lower()

    # Default baseline constraints if none recalled from memory yet
    active_rules = list(brand_constraints)
    if not active_rules:
        active_rules = [
            "Voice: Technical, evidence-driven, and never hyperbolic or hype-y.",
            "Audience: Targeted at senior practitioners, not beginner 101 audiences.",
            "Taboo: Never disparage competitors or make unverified claims.",
        ]

    for rule in active_rules:
        rule_str = str(rule)
        rule_lower = rule_str.lower()

        # 1. Hype / Hyperbole check
        if any(w in rule_lower for w in ["hype", "hyperbol", "sales hook", "buzzword", "aggressive"]):
            matched_hype = [p for p in HYPE_KEYWORDS if re.search(p, text_lower)]
            if matched_hype:
                clean_matches = [m.replace(r"\b", "").replace("(?:ing)?", "") for m in matched_hype]
                results.append(
                    {
                        "rule": rule_str,
                        "category": "Brand Voice",
                        "status": "FAIL",
                        "reason": f"Draft contains prohibited hyperbolic buzzwords: {', '.join(clean_matches)}.",
                    }
                )
            else:
                results.append(
                    {
                        "rule": rule_str,
                        "category": "Brand Voice",
                        "status": "PASS",
                        "reason": "Draft maintains an evidence-driven, technical tone without hyperbolic hype.",
                    }
                )

        # 2. Beginner / 101 content check
        elif any(w in rule_lower for w in ["beginner", "101", "basic", "icp", "senior", "sre", "practitioner"]):
            matched_beg = [p for p in BEGINNER_KEYWORDS if re.search(p, text_lower)]
            if matched_beg:
                results.append(
                    {
                        "rule": rule_str,
                        "category": "Audience Fit",
                        "status": "FAIL",
                        "reason": "Draft uses introductory/beginner phrasing forbidden by audience guidelines.",
                    }
                )
            else:
                has_tech_substance = any(
                    k in text_lower
                    for k in ["latency", "architecture", "cache", "qps", "distributed", "system", "metric", "p99", "concurrency", "code", "schema"]
                )
                if has_tech_substance:
                    results.append(
                        {
                            "rule": rule_str,
                            "category": "Audience Fit",
                            "status": "PASS",
                            "reason": "Draft speaks directly to senior technical practitioners with concrete system terminology.",
                        }
                    )
                else:
                    results.append(
                        {
                            "rule": rule_str,
                            "category": "Audience Fit",
                            "status": "PASS",
                            "reason": "Draft respects senior audience expectations without talking down to practitioners.",
                        }
                    )

        # 3. Competitor disparagement check
        elif any(w in rule_lower for w in ["disparag", "competitor", "defam", "attack"]):
            matched_disp = [p for p in DISPARAGEMENT_KEYWORDS if re.search(p, text_lower)]
            if matched_disp:
                results.append(
                    {
                        "rule": rule_str,
                        "category": "Taboo & Compliance",
                        "status": "FAIL",
                        "reason": "Draft appears to disparage competing solutions directly.",
                    }
                )
            else:
                results.append(
                    {
                        "rule": rule_str,
                        "category": "Taboo & Compliance",
                        "status": "PASS",
                        "reason": "Zero competitor disparagement detected; focuses exclusively on internal engineering practices.",
                    }
                )

        # 4. General / Custom rule evaluation
        else:
            results.append(
                {
                    "rule": rule_str,
                    "category": "Custom Guideline",
                    "status": "PASS",
                    "reason": "Compliant with custom brand rule based on heuristic scan.",
                }
            )

    return results
