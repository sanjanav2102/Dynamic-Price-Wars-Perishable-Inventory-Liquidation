from ai_strategy.provider import LLMDecisionProvider


def test_missing_api_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    expected = object()

    provider = LLMDecisionProvider(
        fallback=lambda: expected
    )

    assert provider.get_decision("test prompt") is expected


def test_invalid_llm_response_uses_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    expected = object()

    provider = LLMDecisionProvider(
        fallback=lambda: expected,
        max_retries=0,
    )

    # With no usable LLM response, provider safely falls back.
    assert provider.get_decision("test prompt") is expected