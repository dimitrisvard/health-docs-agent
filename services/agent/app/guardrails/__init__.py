"""Health-grade guardrails (input + output side).

Posture: answer only from retrieved context; never invent citations; treat document
text as DATA, never instructions (prompt-injection defense); and decline out-of-scope
personal clinical / diagnostic requests with a not-medical-advice message.
"""
from __future__ import annotations

import re

INSUFFICIENT_CONTEXT = (
    "I don't have enough information in the provided documents to answer that."
)

NOT_MEDICAL_ADVICE = (
    "I can't help with personal medical advice — I only summarise the ingested documents, "
    "and this isn't a substitute for a clinician. Ask what the documents say instead "
    "(for example, a drug's listed contraindications or a trial's eligibility criteria)."
)

# Phrases that, inside a retrieved chunk, are attempts to hijack the agent. Document text
# is always treated as data; matches are logged for observability, never obeyed.
_INJECTION = re.compile(
    r"ignore (all |the )?(previous|above|prior) (instructions|prompts?)"
    r"|disregard (the |all )?(previous|above)"
    r"|forget (everything|all|the above)"
    r"|you are now\b"
    r"|new instructions:"
    r"|system prompt\b",
    re.IGNORECASE,
)

# First-person, advice-seeking clinical asks (out of scope). Questions ABOUT the documents
# ("what are the contraindications") are in scope and must NOT match.
_MEDICAL_ADVICE = re.compile(
    r"should i (take|stop|use|start)"
    r"|can i (take|use|stop|mix|combine)"
    r"|is it safe for me"
    r"|what should i do"
    r"|diagnose me"
    r"|do i have\b"
    r"|my (symptoms?|dose|dosage|condition|results?)",
    re.IGNORECASE,
)


def is_supported(chunks: list[dict]) -> bool:
    """A grounded answer requires at least one retrieved chunk."""
    return len(chunks) > 0


def is_medical_advice_request(question: str) -> bool:
    """True for personal clinical/diagnostic asks that should be declined."""
    return bool(_MEDICAL_ADVICE.search(question))


def contains_injection(text: str) -> bool:
    """True if retrieved text looks like a prompt-injection attempt (logged, not obeyed)."""
    return bool(_INJECTION.search(text))
