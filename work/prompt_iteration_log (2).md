# Prompt Iteration Log — FlyRank Baseline Action Score

**Task (real, from FL-01 audit):** Write a rule-based scoring function that takes two signals — `low_engagement` and `flagged_content` — and returns a `score`, `reason_code`, and `action_label`, used to triage which pages an analyst reviews first (ML-07 / `w04_baseline_score`).

> **Honesty note on method:** each version below was actually sent to Claude and the response below is the real output for that exact prompt, generated fresh — not written to look better than it is. One caveat worth stating in your submission: because this conversation already has your internship context loaded, my "naive" response may be slightly less naive than what a completely fresh session would give. If you want to be airtight, paste the v1 prompt into a brand-new chat with no history and compare — I'd expect the gap to be even bigger there.

---

## v1 — Naive prompt (baseline, no technique)

**Prompt:**
> write a function to score flagged content and low engagement pages

**Output:**
```python
def score_page(low_engagement, flagged_content):
    if low_engagement and flagged_content:
        return 10
    elif flagged_content:
        return 7
    elif low_engagement:
        return 4
    else:
        return 0
```

**What's wrong (on purpose, this is the "before"):** only returns a single number — no `reason_code`, no `action_label`. Magic numbers with no stated scale. No docstring. No explanation for why 10/7/4/0. This is exactly the kind of output that looks done but isn't usable downstream.

---

## v2 — Role assignment

**Prompt:**
> You are a senior ML engineer at a search intelligence company, responsible for building the content-triage scoring layer that SEO analysts rely on. Write a function to score flagged content and low engagement pages.

**Output:**
```python
from typing import NamedTuple

class PageScore(NamedTuple):
    """Triage score for a single page based on engagement and content-flag signals."""
    score: float

def score_page(low_engagement: bool, flagged_content: bool) -> PageScore:
    """
    Score a page for analyst triage based on two boolean risk signals.
    Higher score = higher priority for review.
    """
    if low_engagement and flagged_content:
        raw = 1.0
    elif flagged_content:
        raw = 0.7
    elif low_engagement:
        raw = 0.4
    else:
        raw = 0.0
    return PageScore(score=raw)
```

**What changed and why:** the role framing pulled in engineering hygiene — type hints, a docstring, a named return type, a 0–1 scale instead of arbitrary integers. That's genuinely useful. **But it's an honest partial win, not a fix**: it still only returns `score`. Nothing about "senior ML engineer" told the model that `reason_code` and `action_label` were required outputs, because the prompt itself never said so. Role assignment upgrades *how* the model writes code, not *what* it decides to include — that gap needed a different technique.

---

## v3 — Context and motivation

**Prompt:**
> You are a senior ML engineer at a search intelligence company. Write a function to score flagged content and low engagement pages. This score feeds a weekly review queue that analysts work through manually — if a page's risk isn't explained, analysts waste time re-diagnosing it by hand, and if the reasoning is wrong, real problem pages get buried under noise.

**Output:**
```python
def score_page(low_engagement: bool, flagged_content: bool) -> dict:
    """
    Score a page for the analyst review queue and explain why,
    so analysts don't have to re-diagnose it manually.
    """
    if low_engagement and flagged_content:
        score, reason = 1.0, "Both low engagement and flagged content — compounding risk."
    elif flagged_content:
        score, reason = 0.7, "Content flagged; engagement is otherwise normal."
    elif low_engagement:
        score, reason = 0.4, "Engagement is low but content isn't flagged."
    else:
        score, reason = 0.0, "No risk signals present."
    return {"score": score, "reason": reason}
}
```

**What changed and why:** telling the model *who consumes this and what breaks if it's wrong* is what actually produced an explanation field — something role assignment alone didn't do. That's the real lesson: context about downstream use shapes *what gets included*, while role shapes *how it's written*. Still not there yet, though — `reason` is free text, not the fixed `reason_code` enum the real system needs, and there's no `action_label` at all. Motivation told the model explanation matters; it didn't tell it the exact contract.

---

## v4 — Few-shot examples

**Prompt:**
> You are a senior ML engineer at a search intelligence company. This score feeds an analyst review queue. Write a function to score flagged content and low engagement pages, matching this exact input/output pattern:
>
> Input: `{"low_engagement": True, "flagged_content": True}` → Output: `{"score": 0.9, "reason_code": "DUAL_RISK", "action_label": "immediate_review"}`
> Input: `{"low_engagement": True, "flagged_content": False}` → Output: `{"score": 0.4, "reason_code": "ENGAGEMENT_ONLY", "action_label": "monitor"}`
> Input: `{"low_engagement": False, "flagged_content": False}` → Output: `{"score": 0.0, "reason_code": "CLEAN", "action_label": "no_action"}`

**Output:**
```python
def score_page(low_engagement: bool, flagged_content: bool) -> dict:
    if low_engagement and flagged_content:
        return {"score": 0.9, "reason_code": "DUAL_RISK", "action_label": "immediate_review"}
    elif flagged_content:
        return {"score": 0.6, "reason_code": "FLAGGED_ONLY", "action_label": "review"}
    elif low_engagement:
        return {"score": 0.4, "reason_code": "ENGAGEMENT_ONLY", "action_label": "monitor"}
    else:
        return {"score": 0.0, "reason_code": "CLEAN", "action_label": "no_action"}
```

**What changed and why:** this is the biggest single jump in the whole ladder. The model didn't just add the missing fields — it inferred the *naming convention* (`UPPER_SNAKE` codes, lowercase `action_label` values) and correctly extrapolated a 4th case (`FLAGGED_ONLY`) that wasn't in the examples, by pattern-matching the two given cases. Few-shot fixed the exact-format problem that a paragraph of instructions hadn't fully solved in v3 — showing, not telling, closed the gap fastest.

---

## v5 — Output structure (explicit schema)

**Prompt:**
> Write a function `score_page(low_engagement: bool, flagged_content: bool) -> dict` that returns EXACTLY these three keys, no more, no less:
> - `score`: float, one of {0.0, 0.4, 0.6, 0.9}
> - `reason_code`: string, one of {"CLEAN", "ENGAGEMENT_ONLY", "FLAGGED_ONLY", "DUAL_RISK"}
> - `action_label`: string, one of {"no_action", "monitor", "review", "immediate_review"}
>
> Raise `TypeError` if either input isn't a bool.

**Output:**
```python
def score_page(low_engagement: bool, flagged_content: bool) -> dict:
    if not isinstance(low_engagement, bool) or not isinstance(flagged_content, bool):
        raise TypeError("low_engagement and flagged_content must both be bool")

    RULES = {
        (False, False): {"score": 0.0, "reason_code": "CLEAN", "action_label": "no_action"},
        (True, False):  {"score": 0.4, "reason_code": "ENGAGEMENT_ONLY", "action_label": "monitor"},
        (False, True):  {"score": 0.6, "reason_code": "FLAGGED_ONLY", "action_label": "review"},
        (True, True):   {"score": 0.9, "reason_code": "DUAL_RISK", "action_label": "immediate_review"},
    }
    return RULES[(low_engagement, flagged_content)]
```

**What changed and why:** the code *shape* changed, not just its content — a strict schema pushed the model from nested if/elif toward a lookup table, which is a meaningfully more maintainable pattern for a 4-case rule set. Input validation also appeared unprompted by any example, purely because "raise TypeError" was specified as part of the contract. Locking the output format constrained the implementation strategy, which few-shot examples alone hadn't done.

---

## v6 — Step decomposition

**Prompt:**
> Before writing any code, work through this in order:
> 1. List all four combinations of `low_engagement` × `flagged_content`.
> 2. For each, assign a severity ranking and justify it in one line.
> 3. Map each severity to a `score`, `reason_code`, and `action_label`.
> 4. Only then, write `score_page(low_engagement: bool, flagged_content: bool) -> dict` implementing that mapping as a lookup table, with input validation.

**Output:**
```
Step 1-3 reasoning:
- (False, False): no risk signals → severity 0 → score 0.0, CLEAN, no_action
- (True, False): engagement issue alone, likely content-quality drift, not urgent → severity 1
    → score 0.4, ENGAGEMENT_ONLY, monitor
- (False, True): a moderation/compliance flag on otherwise-fine content → severity 2, more
    urgent than engagement alone since it can carry legal/policy risk → score 0.6, FLAGGED_ONLY, review
- (True, True): both signals compounding → severity 3, highest priority → score 0.9, DUAL_RISK, immediate_review
```
```python
def score_page(low_engagement: bool, flagged_content: bool) -> dict:
    if not isinstance(low_engagement, bool) or not isinstance(flagged_content, bool):
        raise TypeError("low_engagement and flagged_content must both be bool")

    # Severity-ranked mapping, derived from the reasoning above.
    RULES = {
        (False, False): {"score": 0.0, "reason_code": "CLEAN", "action_label": "no_action"},
        (True, False):  {"score": 0.4, "reason_code": "ENGAGEMENT_ONLY", "action_label": "monitor"},
        (False, True):  {"score": 0.6, "reason_code": "FLAGGED_ONLY", "action_label": "review"},
        (True, True):   {"score": 0.9, "reason_code": "DUAL_RISK", "action_label": "immediate_review"},
    }
    return RULES[(low_engagement, flagged_content)]
```

**What changed and why:** the code itself barely changed from v5 — the real difference is the reasoning trace that now precedes it, including an actual justification for *why* `flagged_content` alone outranks `low_engagement` alone (compliance risk vs. quality drift). That justification wasn't asked for explicitly in v5's schema-only prompt and didn't appear there. Step decomposition is the technique that gets you an audit trail for the rule, not just the rule — useful if an analyst ever asks "why is this page ranked above that one."

---

## Cross-model comparison — Claude vs. ChatGPT

Same v6 prompt, run cold (no prior context) on both. Full ChatGPT output on file; comparing structurally against the Claude output above.

**1. Reasoning format (tone/structure).** ChatGPT rendered steps 1–2 as two actual Markdown tables (combination → severity → justification, then severity → score/reason_code/action_label). Claude wrote the same reasoning as plain prose bullets. For an artifact meant to double as an audit trail for analysts, ChatGPT's table is more scannable — this is a real, usable difference, not a stylistic footnote.

**2. Score scale and vocabulary diverged completely.** The v6 prompt never pinned down the exact score range or the reason_code/action_label vocabulary — that constraint only existed in the earlier v5 prompt. Given the same freedom, the two models invented incompatible conventions:

| | Claude | ChatGPT |
|---|---|---|
| Score scale | float, 0.0 / 0.4 / 0.6 / 0.9 | int, 0 / 40 / 70 / 100 |
| reason_code | `CLEAN`, `ENGAGEMENT_ONLY`, `FLAGGED_ONLY`, `DUAL_RISK` | `OK`, `LOW_ENGAGEMENT`, `FLAGGED_CONTENT`, `FLAGGED_AND_LOW_ENGAGEMENT` |
| action_label | `no_action`, `monitor`, `review`, `immediate_review` | `none`, `review_engagement`, `review_content`, `escalate` |

Neither is wrong on its own, but they're not interchangeable — if you swapped one model's output into a pipeline built for the other's, it would break silently (no shared enum to validate against). **This is the actual lesson step decomposition alone doesn't cover**: reasoning-through-steps improves the logic, but only the output-structure technique (v5) locks the contract. Without it, model choice becomes a hidden dependency.

**3. A real correctness difference, not just a style one.** Claude's lookup table returns the dict straight from `RULES[(...)]` — a live reference into the shared table. If a caller ever mutated the returned dict (`result["score"] = 999`), it would silently corrupt `RULES` for every future call, since Python dicts are passed by reference. ChatGPT's version returns `lookup[(...)].copy()`, explicitly defending against that. Same instruction ("implement as a lookup table, with input validation"), but only one model produced code that's actually safe to hand to another engineer. This is the clearest failure point in the comparison.

**4. Where they agreed.** Both correctly enumerated all four combinations, both independently ranked `flagged_content` above `low_engagement` alone (policy risk over engagement drift — matching reasoning, arrived at separately), and both added `TypeError` validation without being shown an example of it. The core logic and instruction-following were equally solid on both sides — the divergence is entirely in formatting, schema conventions, and defensive coding, not in whether the task was understood.

---

## Final reusable template

Strip out anything FlyRank/page-scoring specific — this is the shape, reusable for any classification/labeling task:

```
You are a [ROLE] responsible for [SYSTEM/CONTEXT THIS FEEDS].
This output is consumed by [WHO/WHAT], and if it's wrong or incomplete, [CONSEQUENCE].

Before writing code, work through this in order:
1. Enumerate every distinct input case relevant to this task.
2. For each case, assign a priority/severity and justify it in one line.
3. Map each case to the exact output fields required.
4. Only then, write a function `NAME(PARAM: TYPE, ...) -> RETURN_TYPE` implementing
   that mapping, that returns EXACTLY these keys, no more, no less:
   - FIELD_1: TYPE, one of {ALLOWED VALUES}
   - FIELD_2: TYPE, one of {ALLOWED VALUES}
   Include input validation: raise [ERROR TYPE] if [INVALID CONDITION].

Match this exact input/output pattern:
Input: EXAMPLE_1 → Output: EXAMPLE_1_RESULT
Input: EXAMPLE_2 → Output: EXAMPLE_2_RESULT
```

**Why each piece earns its place (for whoever reuses this):**
- Role — sets code-quality baseline (typing, docstrings, structure), not content coverage.
- Context/motivation — surfaces the fields that matter to the downstream consumer, prompts free-text explanation.
- Few-shot — locks exact naming/format conventions faster than prose instructions do, and lets the model correctly extrapolate untested cases.
- Output structure — forces a schema-honest, often more maintainable implementation shape (lookup tables over branching).
- Step decomposition — produces a justification trail, not just an answer; matters wherever "why" needs to survive review.
