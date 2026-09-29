# EchoMind reviewer demo

**Length:** 75 seconds  
**Story:** a remembered critique changes the next recommendation.

## Prepare

- Start the app with `HINDSIGHT_USE_MOCK=true` and an empty `LLM_API_KEY` for a repeatable offline demo, or use a reachable Hindsight bank.
- Open the **Memory** page once and seed demo memory for **EchoMind AI**. This keeps brand facts and a belief available for the learning cycle.
- Return to **Overview** before starting the timer.

## Script

**0:00–0:08 | The problem**  
Say: “Stateless writing tools forget what a team rejected. They repeat the same format and make you explain the brand again.”  
Show the EchoMind title and the page navigation.

**0:08–0:18 | Overview gap**  
Say: “EchoMind starts with measured history. Engineering Culture is at 6.7% against a 20% target, while architecture is already over target.”  
Point to the pillar allocation chart and the gaps/saturation rows.

**0:18–0:31 | Strategy provenance**  
Say: “The strategy page explains why this pillar, why now, and why this format. This provenance row ties the choice to measured performance; the memory rows show which brand rules and beliefs were recalled.”  
Generate the recommendation and point to the rationale and provenance table.

**0:31–0:47 | Learn from rejection**  
Say: “I reject the generic angle and ask for code and an incident timeline. One learning cycle records that critique, then recommends again.”  
On **Learning**, run **Run learning cycle**. Point to the changed angle, switched format, confidence delta, and the recalled rejection text.

**0:47–0:57 | Belief timeline**  
Say: “The memory page exposes what the agent learned, why, the supporting evidence pointers, and the confidence recorded with the belief.”  
Show the filtered belief list and confidence timeline.

**0:57–1:08 | Guardrail check**  
Say: “Before a draft is used, deterministic checks report pass or fail with a reason for each brand rule.”  
Return to **Strategy**, generate a draft, and point to the guardrail table.

**1:08–1:15 | Close**  
Say: “The important part is visible: a remembered critique changed the plan, and every decision remains auditable.”
