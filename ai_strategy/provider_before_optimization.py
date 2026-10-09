
"""Local Ollama decision provider with Pydantic validation and fallback."""

import json
import os
import re
from typing import Callable, Optional
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from pydantic import ValidationError

from models.schemas import ActionType, Decision

load_dotenv()


class LLMDecisionProvider:
    """Generate validated decisions using local Ollama."""

    def __init__(
        self,
        fallback: Optional[Callable[[], Decision]] = None,
        model: Optional[str] = None,
        max_retries: int = 0,
        timeout: float = 30.0,
        enabled: Optional[bool] = None,
    ):
        self.fallback = fallback
        self.model = (
            model
            or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        )
        self.base_url = os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        ).rstrip("/")
        self.max_retries = max(0, max_retries)
        self.timeout = timeout

        if enabled is None:
            self.enabled = os.getenv(
                "AI_ENABLED", "false"
            ).lower() in {"1", "true", "yes", "on"}
        else:
            self.enabled = enabled

        self.last_source = "disabled"
        self.last_error = None

    def get_decision(
        self,
        prompt: str,
        fallback: Optional[Callable[[], Decision]] = None,
    ) -> Decision:
        """Return a validated model decision or deterministic fallback."""
        fallback_fn = fallback or self.fallback

        if not self.enabled:
            self.last_source = "disabled"
            self.last_error = None
            return self._use_fallback(fallback_fn)

        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": (
                        "You are a decision-making agent in a perishable "
                        "inventory negotiation simulation.\n"
                        "Return ONLY one JSON object matching this shape:\n"
                        '{"action":"walk_away","offer":null,'
                        '"reason":"brief explanation"}\n'
                        "Allowed actions: offer, counter, accept, reject, "
                        "walk_away.\n"
                        "If an offer is required, include an offer object "
                        "with seller_id, buyer_id, quantity, price_per_unit, "
                        "and minimum_remaining_shelf_life_days.\n"
                        "Use only facts from the prompt. Follow all business "
                        "constraints described in the prompt.\n\n"
                        f"Decision context:\n{prompt}"
                    ),
                    "stream": False,
                    "format": "json",
                    "options": {
                    "temperature": 0,
                    "num_predict": 100,
                },
                }

                request = Request(
                    f"{self.base_url}/api/generate",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )

                with urlopen(request, timeout=self.timeout) as response:
                    body = json.loads(response.read().decode("utf-8"))

                content = body.get("response", "").strip()
                if not content:
                    raise ValueError("Ollama returned empty content.")

                # Be tolerant if a model wraps JSON in Markdown fences.
                content = re.sub(
                    r"^```(?:json)?\s*|\s*```$",
                    "",
                    content,
                    flags=re.IGNORECASE,
                ).strip()

                decision = Decision.model_validate_json(content)
                self._validate_decision(decision)

                self.last_source = "ai"
                self.last_error = None
                return decision

            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                self.last_error = (
                    f"Invalid Ollama response (attempt {attempt + 1}): {exc}"
                )
            except Exception as exc:
                self.last_error = (
                    f"Ollama error (attempt {attempt + 1}): {exc}"
                )

        self.last_source = "fallback"
        return self._use_fallback(fallback_fn)

    @staticmethod
    def _validate_decision(decision: Decision) -> None:
        if decision.action in {ActionType.ACCEPT, ActionType.COUNTER}:
            if decision.offer is None:
                raise ValueError(
                    f"{decision.action.value} decisions require an offer."
                )

    @staticmethod
    def _use_fallback(
        fallback_fn: Optional[Callable[[], Decision]],
    ) -> Decision:
        if fallback_fn is None:
            raise RuntimeError(
                "No deterministic fallback decision was supplied."
            )
        return fallback_fn()
