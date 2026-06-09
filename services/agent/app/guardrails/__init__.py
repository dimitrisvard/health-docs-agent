"""Output-side guardrails.

TODO(Phase 6): grounded-only check (refuse when no supporting chunk), not-medical-advice
posture, prompt-injection detection. Write tests FIRST:
  - no-context question -> refusal
  - document containing 'ignore previous instructions' -> treated as data, ignored
"""
