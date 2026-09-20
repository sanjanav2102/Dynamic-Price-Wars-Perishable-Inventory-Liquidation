"""Optional LLM decision provider with validation and safe fallback."""

import os
from typing import Callable

from pydantic import ValidationError

from models.schemas import Decision


class LLMDecisionProvider:
    """Generate validated decisions using an LLM, or fall back safely."""

    def __init__(
        self,
        fallback: Callable[[], Decision],
        model: str | None = None,
        max_retries: int = 2,
        timeout: float = 10.0,
    ):
        self.fallback = fallback
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = max(0, max_retries)
        self.timeout = timeout
        self.api_key = os.getenv("OPENAI_API_KEY")

    def get_decision(self, prompt: str) -> Decision:
        """Return a schema-valid decision, using fallback on failure."""

        if not self.api_key:
            return self.fallback()

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=0,
            )

            for _ in range(self.max_retries + 1):
                try:
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Return a decision matching the "
                                    "required JSON schema."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                    )

                    content = response.choices[0].message.content
                    if not content:
                        continue

                    return Decision.model_validate_json(content)

                except (ValidationError, ValueError):
                    continue
                except Exception:
                    # Network, API, timeout, or provider error.
                    continue

        except Exception:
            # OpenAI package/client unavailable or setup failure.
            pass

        return self.fallback()