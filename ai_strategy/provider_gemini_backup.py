# # """Optional LLM decision provider with validation and safe fallback."""

# # import os
# # from typing import Callable

# # from pydantic import ValidationError

# # from models.schemas import Decision


# # class LLMDecisionProvider:
# #     """Generate validated decisions using an LLM, or fall back safely."""

# #     def __init__(
# #         self,
# #         fallback: Callable[[], Decision],
# #         model: str | None = None,
# #         max_retries: int = 2,
# #         timeout: float = 10.0,
# #     ):
# #         self.fallback = fallback
# #         self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# #         self.max_retries = max(0, max_retries)
# #         self.timeout = timeout
# #         self.api_key = os.getenv("OPENAI_API_KEY")

# #     def get_decision(self, prompt: str) -> Decision:
# #         """Return a schema-valid decision, using fallback on failure."""

# #         if not self.api_key:
# #             return self.fallback()

# #         try:
# #             from openai import OpenAI

# #             client = OpenAI(
# #                 api_key=self.api_key,
# #                 timeout=self.timeout,
# #                 max_retries=0,
# #             )

# #             for _ in range(self.max_retries + 1):
# #                 try:
# #                     response = client.chat.completions.create(
# #                         model=self.model,
# #                         messages=[
# #                             {
# #                                 "role": "system",
# #                                 "content": (
# #                                     "Return a decision matching the "
# #                                     "required JSON schema."
# #                                 ),
# #                             },
# #                             {"role": "user", "content": prompt},
# #                         ],
# #                         response_format={"type": "json_object"},
# #                     )

# #                     content = response.choices[0].message.content
# #                     if not content:
# #                         continue

# #                     return Decision.model_validate_json(content)

# #                 except (ValidationError, ValueError):
# #                     continue
# #                 except Exception:
# #                     # Network, API, timeout, or provider error.
# #                     continue

# #         except Exception:
# #             # OpenAI package/client unavailable or setup failure.
# #             pass

# #         return self.fallback()
# '''Your current provider already has the right foundation, but this version adds:

# AI_ENABLED
# .env loading
# retries
# timeout
# structured Pydantic validation
# invalid-response fallback
# API failure fallback
# source tracking: AI / fallback / disabled

# This preserves the fallback requirement from your project specification'''
# """
# LLM decision provider.

# Responsibilities:
# - Connect to the OpenAI API when AI is enabled.
# - Request structured decisions.
# - Validate every response using the shared Pydantic Decision model.
# - Retry bounded API failures.
# - Fall back to deterministic rule-based decisions.
# - Never modify the simulation environment directly.
# """

# import json
# import os
# from typing import Callable, Optional

# from dotenv import load_dotenv
# from pydantic import ValidationError

# from models.schemas import Decision, ActionType


# load_dotenv()


# class LLMDecisionProvider:
#     """
#     Optional LLM decision provider with deterministic fallback.

#     The provider never changes inventory, budget, or market state.
#     It only returns a Decision object.
#     """

#     def __init__(
#         self,
#         fallback: Optional[Callable[[], Decision]] = None,
#         model: Optional[str] = None,
#         max_retries: int = 2,
#         timeout: float = 10.0,
#         enabled: Optional[bool] = None,
#     ):
#         self.fallback = fallback

#         self.model = (
#             model
#             or os.getenv(
#                 "OPENAI_MODEL",
#                 "gpt-4o-mini",
#             )
#         )

#         self.max_retries = max(
#             0,
#             max_retries,
#         )

#         self.timeout = timeout

#         self.api_key = os.getenv(
#             "OPENAI_API_KEY"
#         )

#         if enabled is None:
#             enabled_value = os.getenv(
#                 "AI_ENABLED",
#                 "false",
#             )

#             self.enabled = (
#                 enabled_value.lower()
#                 in {
#                     "1",
#                     "true",
#                     "yes",
#                     "on",
#                 }
#             )
#         else:
#             self.enabled = enabled

#         self.last_source = "disabled"
#         self.last_error = None

#     # =========================================================
#     # Public API
#     # =========================================================

#     def get_decision(
#         self,
#         prompt: str,
#         fallback: Optional[
#             Callable[[], Decision]
#         ] = None,
#     ) -> Decision:
#         """
#         Get a decision from the LLM.

#         If AI is disabled, unavailable, invalid,
#         or times out, use the deterministic fallback.
#         """

#         fallback_fn = (
#             fallback
#             or self.fallback
#         )

#         if not self.enabled:
#             self.last_source = "disabled"
#             self.last_error = None

#             return self._use_fallback(
#                 fallback_fn
#             )

#         if not self.api_key:
#             self.last_source = "fallback"
#             self.last_error = (
#                 "OPENAI_API_KEY is not configured."
#             )

#             return self._use_fallback(
#                 fallback_fn
#             )

#         try:
#             from openai import OpenAI

#             client = OpenAI(
#                 api_key=self.api_key,
#                 timeout=self.timeout,
#                 max_retries=0,
#             )

#         except Exception as exc:
#             self.last_source = "fallback"
#             self.last_error = str(exc)

#             return self._use_fallback(
#                 fallback_fn
#             )

#         for attempt in range(
#             self.max_retries + 1
#         ):
#             try:
#                 response = (
#                     client
#                     .chat
#                     .completions
#                     .create(
#                         model=self.model,
#                         messages=[
#                             {
#                                 "role": "system",
#                                 "content": (
#                                     "You are an agent in a "
#                                     "multi-agent perishable "
#                                     "inventory negotiation "
#                                     "simulation.\n\n"
#                                     "Return ONLY valid JSON "
#                                     "matching the supplied "
#                                     "Decision schema.\n\n"
#                                     "Do not return markdown. "
#                                     "Do not explain the JSON "
#                                     "outside the JSON object."
#                                 ),
#                             },
#                             {
#                                 "role": "user",
#                                 "content": prompt,
#                             },
#                         ],
#                         response_format={
#                             "type": "json_object"
#                         },
#                     )
#                 )

#                 content = (
#                     response
#                     .choices[0]
#                     .message
#                     .content
#                 )

#                 if not content:
#                     raise ValueError(
#                         "LLM returned empty content."
#                     )

#                 decision = (
#                     Decision
#                     .model_validate_json(
#                         content
#                     )
#                 )

#                 self._validate_decision(
#                     decision
#                 )

#                 self.last_source = "ai"
#                 self.last_error = None

#                 return decision

#             except (
#                 ValidationError,
#                 ValueError,
#                 json.JSONDecodeError,
#             ) as exc:

#                 self.last_error = (
#                     f"Invalid LLM response "
#                     f"(attempt {attempt + 1}): "
#                     f"{exc}"
#                 )

#                 continue

#             except Exception as exc:

#                 self.last_error = (
#                     f"LLM/API error "
#                     f"(attempt {attempt + 1}): "
#                     f"{exc}"
#                 )

#                 continue

#         self.last_source = "fallback"

#         return self._use_fallback(
#             fallback_fn
#         )

#     # =========================================================
#     # Validation
#     # =========================================================

#     @staticmethod
#     def _validate_decision(
#         decision: Decision,
#     ) -> None:
#         """
#         Perform semantic validation in addition
#         to Pydantic validation.
#         """

#         action = decision.action

#         if action in {
#             ActionType.ACCEPT,
#             ActionType.COUNTER,
#         }:
#             if decision.offer is None:
#                 raise ValueError(
#                     "Accept/counter decisions "
#                     "must contain an offer."
#                 )

#         if decision.reason is None:
#             raise ValueError(
#                 "Decision must contain a reason."
#             )

#     # =========================================================
#     # Fallback
#     # =========================================================

#     def _use_fallback(
#         self,
#         fallback_fn: Optional[
#             Callable[[], Decision]
#         ],
#     ) -> Decision:

#         if fallback_fn is None:
#             raise RuntimeError(
#                 "No deterministic fallback decision "
#                 "was supplied."
#             )

#         return fallback_fn()
"""
Gemini-based LLM decision provider.

Responsibilities:
- Connect to Google Gemini when AI is enabled.
- Request structured negotiation decisions.
- Validate every response using the shared Pydantic Decision model.
- Retry bounded API failures.
- Fall back to deterministic rule-based decisions.
- Never modify the simulation environment directly.
"""

import json
import os
from typing import Callable, Optional

from dotenv import load_dotenv
from pydantic import ValidationError

from models.schemas import Decision, ActionType


load_dotenv()


class LLMDecisionProvider:
    """
    Optional Gemini decision provider with deterministic fallback.

    The provider only generates Decision objects.

    It does NOT:
    - modify inventory
    - modify retailer budgets
    - execute deals
    - modify market state
    """

    def __init__(
        self,
        fallback: Optional[Callable[[], Decision]] = None,
        model: Optional[str] = None,
        max_retries: int = 2,
        timeout: float = 15.0,
        enabled: Optional[bool] = None,
    ):
        self.fallback = fallback

        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                "gemini-3.6-flash",
            )
        )

        self.max_retries = max(
            0,
            max_retries,
        )

        self.timeout = timeout

        self.api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if enabled is None:
            enabled_value = os.getenv(
                "AI_ENABLED",
                "false",
            )

            self.enabled = (
                enabled_value.lower()
                in {
                    "1",
                    "true",
                    "yes",
                    "on",
                }
            )
        else:
            self.enabled = enabled

        self.last_source = "disabled"
        self.last_error = None

    # =========================================================
    # PUBLIC API
    # =========================================================

    def get_decision(
        self,
        prompt: str,
        fallback: Optional[
            Callable[[], Decision]
        ] = None,
    ) -> Decision:
        """
        Ask Gemini for a decision.

        If Gemini is disabled, unavailable, returns invalid
        data, or fails, use the deterministic fallback.
        """

        fallback_fn = (
            fallback
            or self.fallback
        )

        # -----------------------------------------------------
        # AI disabled
        # -----------------------------------------------------

        if not self.enabled:
            self.last_source = "disabled"
            self.last_error = None

            return self._use_fallback(
                fallback_fn
            )

        # -----------------------------------------------------
        # Missing API key
        # -----------------------------------------------------

        if not self.api_key:
            self.last_source = "fallback"

            self.last_error = (
                "GEMINI_API_KEY is not configured."
            )

            return self._use_fallback(
                fallback_fn
            )

        # -----------------------------------------------------
        # Import Gemini SDK
        # -----------------------------------------------------

        try:
            from google import genai

            client = genai.Client(
                api_key=self.api_key
            )

        except Exception as exc:
            self.last_source = "fallback"
            self.last_error = str(exc)

            return self._use_fallback(
                fallback_fn
            )

        # -----------------------------------------------------
        # Gemini attempts
        # -----------------------------------------------------

        for attempt in range(
            self.max_retries + 1
        ):

            try:
                response = (
                    client.models.generate_content(
                        model=self.model,
                        contents=(
                            self._build_prompt(
                                prompt
                            )
                        ),
                    )
                )

                content = self._extract_text(
                    response
                )

                if not content:
                    raise ValueError(
                        "Gemini returned empty content."
                    )

                content = (
                    self._clean_json(
                        content
                    )
                )

                decision = (
                    Decision.model_validate_json(
                        content
                    )
                )

                self._validate_decision(
                    decision
                )

                self.last_source = "ai"
                self.last_error = None

                return decision

            except (
                ValidationError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:

                self.last_error = (
                    "Invalid Gemini response "
                    f"(attempt {attempt + 1}): "
                    f"{exc}"
                )

                continue

            except Exception as exc:

                self.last_error = (
                    "Gemini/API error "
                    f"(attempt {attempt + 1}): "
                    f"{exc}"
                )

                continue

        # -----------------------------------------------------
        # All attempts failed
        # -----------------------------------------------------

        self.last_source = "fallback"

        return self._use_fallback(
            fallback_fn
        )

    # =========================================================
    # PROMPT
    # =========================================================

    @staticmethod
    def _build_prompt(
        prompt: str,
    ) -> str:
        """
        Add strict instructions around the existing
        project-specific prompt.
        """

        return f"""
You are an intelligent negotiation agent in a
multi-agent perishable inventory simulation.

You MUST return exactly one JSON object.

The JSON must represent this structure:

{{
  "action": "accept" | "counter" | "walk_away" | "reject",
  "offer": {{
    "buyer_id": "string",
    "seller_id": "string",
    "price_per_unit": number,
    "quantity": integer,
    "minimum_remaining_shelf_life_days": integer
  }},
  "reason": "short explanation"
}}

Important rules:

1. Return JSON only.
2. Do not use Markdown.
3. Do not put ``` around the JSON.
4. Do not invent fields.
5. Do not modify the simulation environment.
6. Respect all constraints given in the user prompt.
7. For ACCEPT and COUNTER, include an offer.
8. For WALK_AWAY or REJECT, the offer may be omitted.
9. Prices must be positive.
10. Quantities must be positive.
11. Preserve buyer and seller IDs from the negotiation.
12. Respect budgets, capacity, inventory, willingness to pay,
    reservation price, and shelf-life constraints.

PROJECT NEGOTIATION CONTEXT:

{prompt}
"""

    # =========================================================
    # RESPONSE EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_text(
        response,
    ) -> str:
        """
        Extract text from Gemini response safely.
        """

        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            return text.strip()

        # Defensive fallback for SDK response formats.
        candidates = getattr(
            response,
            "candidates",
            None,
        )

        if candidates:
            for candidate in candidates:

                content = getattr(
                    candidate,
                    "content",
                    None,
                )

                if content is None:
                    continue

                parts = getattr(
                    content,
                    "parts",
                    None,
                )

                if not parts:
                    continue

                for part in parts:

                    text_part = getattr(
                        part,
                        "text",
                        None,
                    )

                    if text_part:
                        return text_part.strip()

        return ""

    # =========================================================
    # JSON CLEANING
    # =========================================================

    @staticmethod
    def _clean_json(
        content: str,
    ) -> str:
        """
        Remove accidental Markdown fences or surrounding text.
        """

        content = content.strip()

        if content.startswith(
            "```json"
        ):
            content = content[
                len("```json"):
            ]

        elif content.startswith(
            "```"
        ):
            content = content[
                len("```"):
            ]

        if content.endswith(
            "```"
        ):
            content = content[
                :-len("```")
            ]

        content = content.strip()

        # If Gemini added explanatory text around the JSON,
        # extract the outermost JSON object.
        start = content.find("{")
        end = content.rfind("}")

        if start >= 0 and end >= start:
            content = content[
                start:end + 1
            ]

        return content.strip()

    # =========================================================
    # SEMANTIC VALIDATION
    # =========================================================

    @staticmethod
    def _validate_decision(
        decision: Decision,
    ) -> None:
        """
        Perform semantic validation in addition to Pydantic
        validation.
        """

        action = decision.action

        if action in {
            ActionType.ACCEPT,
            ActionType.COUNTER,
        }:

            if decision.offer is None:
                raise ValueError(
                    "Accept/counter decisions "
                    "must contain an offer."
                )

        if decision.reason is None:
            raise ValueError(
                "Decision must contain a reason."
            )

    # =========================================================
    # FALLBACK
    # =========================================================

    def _use_fallback(
        self,
        fallback_fn: Optional[
            Callable[[], Decision]
        ],
    ) -> Decision:
        """
        Execute deterministic fallback.
        """

        if fallback_fn is None:
            raise RuntimeError(
                "No deterministic fallback decision "
                "was supplied."
            )

        return fallback_fn()