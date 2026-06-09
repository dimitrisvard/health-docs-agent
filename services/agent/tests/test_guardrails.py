from app.guardrails import INSUFFICIENT_CONTEXT, is_supported


def test_is_supported_requires_at_least_one_chunk():
    assert is_supported([]) is False
    assert is_supported([{"id": 1}]) is True


def test_refusal_message_is_grounded_and_safe():
    assert "don't have enough information" in INSUFFICIENT_CONTEXT.lower()
