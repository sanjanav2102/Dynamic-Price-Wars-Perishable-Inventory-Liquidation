
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
        fallback=None,
        model=None,
        max_retries=0,
        timeout=45.0,
        enabled=None,
        max_ai_calls=10,
        
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

        self.max_ai_calls = max(0, max_ai_calls)
        self.ai_calls_made = 0
        self.last_source = "disabled"
        self.last_error = None

    def get_decision(
        self,
        prompt: str,
        fallback: Optional[Callable[[], Decision]] = None,
    ) -> Decision:
        """Return a validated model decision or deterministic fallback."""
        fallback_fn = fallback or self.fallback
        print(
    f"[OLLAMA DEBUG] enabled={self.enabled}, "
    f"calls_made={self.ai_calls_made}, "
    f"max_calls={self.max_ai_calls}"
)

        if not self.enabled:
            self.last_source = "disabled"
            self.last_error = None
            return self._use_fallback(fallback_fn)
        if self.ai_calls_made >= self.max_ai_calls:
            self.last_source = "fallback"
            self.last_error = "AI call limit reached; using rule-based fallback."
            print(f"[OLLAMA DEBUG] {self.last_error}")
            return self._use_fallback(fallback_fn)
        self.ai_calls_made += 1
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
                        "num_predict": 128,
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
                print(f"[OLLAMA DEBUG] Raw model response: {content!r}")
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
                print("[OLLAMA DEBUG] Successfully received a valid AI decision.")
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
        print(f"[OLLAMA DEBUG] Falling back: {self.last_error}")
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
