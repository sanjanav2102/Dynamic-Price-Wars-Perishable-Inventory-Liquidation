
import os

import pytest

from ai_strategy.provider import LLMDecisionProvider
from models.schemas import Decision


def make_fallback() -> Decision:
    """Create a valid local decision without calling Gemini."""
    return Decision.model_validate({
        "action": "walk_away",
        "reason": "Deterministic fallback test.",
    })


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GEMINI_TESTS") != "1",
    reason="Live Gemini tests are disabled by default.",
)
def test_gemini_provider_can_return_ai_decision():
    """Make one live request and report the provider's actual error."""

    provider = LLMDecisionProvider(
        enabled=True,
        max_retries=0,  # Avoid extra API requests during diagnosis.
    )

    result = provider.get_decision(
        """
Return a valid decision using the project's decision schema.
Choose action "walk_away" and reason "Gemini integration test".
Do not include an offer for this action.
""",
        fallback=make_fallback,
    )

    assert provider.last_source == "ai", (
        "Gemini did not produce a valid AI decision. "
        f"Source: {provider.last_source}; "
        f"Error: {provider.last_error}"
    )

    assert result.action.value == "walk_away"


def test_provider_falls_back_when_disabled():
    """A disabled provider must use the local deterministic fallback."""
    provider = LLMDecisionProvider(enabled=False, max_retries=0)

    result = provider.get_decision(
        "This test should use the local fallback.",
        fallback=make_fallback,
    )

    assert isinstance(result, Decision)
    assert result.action.value == "walk_away"
    assert provider.last_source == "disabled"

