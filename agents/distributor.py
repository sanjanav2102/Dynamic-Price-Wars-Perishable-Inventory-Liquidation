# # """Distributor agent.

# # The distributor seeks a reasonable price and liquidation before expiry.
# # Deterministic business constraints take priority over optional LLM suggestions.
# # """

# # import os
# # from typing import Optional

# # from agents.base_agent import BaseAgent
# # from ai_strategy.provider import LLMDecisionProvider
# # from ai_strategy.prompts import distributor_response_prompt
# # from models.schemas import ActionType, Decision, MarketState, Offer


# # class DistributorAgent(BaseAgent):
# #     def __init__(
# #         self,
# #         agent_id: str = "distributor",
# #         ai_enabled: Optional[bool] = None,
# #     ):
# #         super().__init__(agent_id)

# #         if ai_enabled is None:
# #             value = os.getenv("AI_ENABLED", "false")
# #             ai_enabled = value.strip().lower() in {"1", "true", "yes", "on"}

# #         self.ai_enabled = ai_enabled
# #         self.ai_provider = LLMDecisionProvider(
# #             enabled=ai_enabled,
# #             timeout=45.0,
# #             max_ai_calls=10,
# #         )
# #         self.last_decision_source = "RULE"

# #     def respond_to_offer(
# #         self,
# #         offer: Offer,
# #         market_state: MarketState,
# #     ) -> Decision:
# #         """Apply hard rules first; consult AI only for genuine negotiation."""
# #         rule_decision = self._rule_based_response(offer, market_state)

# #         # Invalid offers and offers that already satisfy the seller's rules
# #         # have deterministic outcomes. AI must not override them.
# #         if rule_decision.action in {ActionType.ACCEPT, ActionType.REJECT}:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         if not self.ai_enabled:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         prompt = distributor_response_prompt(
# #             market_state=market_state,
# #             incoming_offer=offer,
# #         )
# #         decision = self.ai_provider.get_decision(
# #             prompt,
# #             fallback=lambda: rule_decision,
# #         )

# #         validated = self._validate_ai_decision(
# #             decision,
# #             offer,
# #             market_state,
# #         )
# #         if validated is None:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         self.last_decision_source = (
# #             "AI" if self.ai_provider.last_source == "ai" else "FALLBACK"
# #         )
# #         return validated

# #     def _rule_based_response(
# #         self,
# #         offer: Offer,
# #         market_state: MarketState,
# #     ) -> Decision:
# #         """Return deterministic accept/reject/counter based on hard constraints."""
# #         reservation_price = market_state.distributor_reservation_price

# #         if offer.price_per_unit <= 0 or offer.quantity <= 0:
# #             return Decision(
# #                 action=ActionType.REJECT,
# #                 reason="Offer price and quantity must be positive.",
# #             )

# #         if offer.quantity > market_state.available_quantity:
# #             return Decision(
# #                 action=ActionType.REJECT,
# #                 reason="Offer quantity exceeds available inventory.",
# #             )

# #         if market_state.remaining_shelf_life_days < offer.minimum_remaining_shelf_life_days:
# #             return Decision(
# #                 action=ActionType.REJECT,
# #                 reason="Offer requires more shelf life than the inventory has.",
# #             )

# #         if offer.price_per_unit >= reservation_price:
# #             return Decision(
# #                 action=ActionType.ACCEPT,
# #                 offer=offer,
# #                 reason=(
# #                     "Offer meets or exceeds distributor reservation price "
# #                     "and inventory/shelf-life constraints."
# #                 ),
# #             )

# #         # Never counter below reservation price.
# #         counter_offer = Offer(
# #             buyer_id=offer.buyer_id,
# #             seller_id=self.agent_id,
# #             price_per_unit=round(reservation_price, 2),
# #             quantity=offer.quantity,
# #             minimum_remaining_shelf_life_days=(
# #                 offer.minimum_remaining_shelf_life_days
# #             ),
# #         )
# #         return Decision(
# #             action=ActionType.COUNTER,
# #             offer=counter_offer,
# #             reason=(
# #                 "Offer is below reservation price; distributor counters "
# #                 "at its reservation price."
# #             ),
# #         )

# #     def _validate_ai_decision(
# #         self,
# #         decision: Decision,
# #         incoming_offer: Offer,
# #         market_state: MarketState,
# #     ) -> Optional[Decision]:
# #         """Validate AI output; never let it bypass deterministic constraints."""
# #         reservation = market_state.distributor_reservation_price

# #         if decision.action == ActionType.ACCEPT:
# #             # Only accept the original incoming offer if it meets all rules.
# #             if (
# #                 incoming_offer.price_per_unit < reservation
# #                 or incoming_offer.price_per_unit <= 0
# #                 or incoming_offer.quantity <= 0
# #                 or incoming_offer.quantity > market_state.available_quantity
# #                 or market_state.remaining_shelf_life_days
# #                 < incoming_offer.minimum_remaining_shelf_life_days
# #             ):
# #                 return None
# #             return Decision(
# #                 action=ActionType.ACCEPT,
# #                 offer=incoming_offer,
# #                 reason=decision.reason or "AI accepted a valid offer.",
# #             )

# #         if decision.action == ActionType.REJECT:
# #             return Decision(
# #                 action=ActionType.REJECT,
# #                 reason=decision.reason or "AI rejected the offer.",
# #             )

# #         if decision.action == ActionType.COUNTER:
# #             counter = decision.offer
# #             if counter is None:
# #                 return None
# #             if (
# #                 counter.seller_id != self.agent_id
# #                 or counter.buyer_id != incoming_offer.buyer_id
# #                 or counter.price_per_unit < reservation
# #                 or counter.price_per_unit <= 0
# #                 or counter.quantity <= 0
# #                 or counter.quantity > market_state.available_quantity
# #                 or market_state.remaining_shelf_life_days
# #                 < counter.minimum_remaining_shelf_life_days
# #             ):
# #                 return None
# #             return Decision(
# #                 action=ActionType.COUNTER,
# #                 offer=counter,
# #                 reason=decision.reason or "AI generated a valid counteroffer.",
# #             )

# #         return None
# """Distributor agent.

# The distributor seeks a reasonable price and liquidation before expiry.
# Deterministic business constraints take priority over optional LLM suggestions.
# """

# import os
# from typing import Optional

# from agents.base_agent import BaseAgent
# from ai_strategy.provider import LLMDecisionProvider
# from ai_strategy.prompts import distributor_response_prompt
# from models.schemas import ActionType, Decision, MarketState, Offer


# class DistributorAgent(BaseAgent):
#     def __init__(
#         self,
#         agent_id: str = "distributor",
#         ai_enabled: Optional[bool] = None,
#     ):
#         super().__init__(agent_id)

#         if ai_enabled is None:
#             value = os.getenv("AI_ENABLED", "false")
#             ai_enabled = value.strip().lower() in {"1", "true", "yes", "on"}

#         self.ai_enabled = ai_enabled
#         self.ai_provider = LLMDecisionProvider(
#             enabled=ai_enabled,
#             timeout=45.0,
#             max_ai_calls=10,
#         )
#         self.last_decision_source = "RULE"
#         # Observability only; these counters do not change negotiation rules.
#         self.ai_metrics = {
#             "ai_attempts": 0,
#             "ai_responses_received": 0,
#             "ai_decisions_used": 0,
#             "fallbacks": 0,
#         }

#     def respond_to_offer(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         """Apply hard rules first; consult AI only for genuine negotiation."""
#         rule_decision = self._rule_based_response(offer, market_state)

#         # Invalid offers and offers that already satisfy the seller's rules
#         # have deterministic outcomes. AI must not override them.
#         if rule_decision.action in {ActionType.ACCEPT, ActionType.REJECT}:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         if not self.ai_enabled:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         prompt = distributor_response_prompt(
#             market_state=market_state,
#             incoming_offer=offer,
#         )
#         if self.ai_enabled:
#             self.ai_metrics["ai_attempts"] += 1
#         decision = self.ai_provider.get_decision(
#             prompt,
#             fallback=lambda: rule_decision,
#         )

#         if self.ai_provider.last_source == "ai":
#             self.ai_metrics["ai_responses_received"] += 1
#         elif self.ai_provider.last_source == "fallback":
#             self.ai_metrics["fallbacks"] += 1

#         validated = self._validate_ai_decision(
#             decision,
#             offer,
#             market_state,
#         )
#         if validated is None:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         self.last_decision_source = (
#             "AI" if self.ai_provider.last_source == "ai" else "FALLBACK"
#         )
#         if self.last_decision_source == "AI":
#             self.ai_metrics["ai_decisions_used"] += 1
#         elif self.ai_provider.last_source == "fallback":
#             self.ai_metrics["fallbacks"] += 1
#         return validated

#     def _rule_based_response(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         """Return deterministic accept/reject/counter based on hard constraints."""
#         reservation_price = market_state.distributor_reservation_price

#         if offer.price_per_unit <= 0 or offer.quantity <= 0:
#             return Decision(
#                 action=ActionType.REJECT,
#                 reason="Offer price and quantity must be positive.",
#             )

#         if offer.quantity > market_state.available_quantity:
#             return Decision(
#                 action=ActionType.REJECT,
#                 reason="Offer quantity exceeds available inventory.",
#             )

#         if market_state.remaining_shelf_life_days < offer.minimum_remaining_shelf_life_days:
#             return Decision(
#                 action=ActionType.REJECT,
#                 reason="Offer requires more shelf life than the inventory has.",
#             )

#         if offer.price_per_unit >= reservation_price:
#             return Decision(
#                 action=ActionType.ACCEPT,
#                 offer=offer,
#                 reason=(
#                     "Offer meets or exceeds distributor reservation price "
#                     "and inventory/shelf-life constraints."
#                 ),
#             )

#         # Never counter below reservation price.
#         counter_offer = Offer(
#             buyer_id=offer.buyer_id,
#             seller_id=self.agent_id,
#             price_per_unit=round(reservation_price, 2),
#             quantity=offer.quantity,
#             minimum_remaining_shelf_life_days=(
#                 offer.minimum_remaining_shelf_life_days
#             ),
#         )
#         return Decision(
#             action=ActionType.COUNTER,
#             offer=counter_offer,
#             reason=(
#                 "Offer is below reservation price; distributor counters "
#                 "at its reservation price."
#             ),
#         )

#     def _validate_ai_decision(
#         self,
#         decision: Decision,
#         incoming_offer: Offer,
#         market_state: MarketState,
#     ) -> Optional[Decision]:
#         """Validate AI output; never let it bypass deterministic constraints."""
#         reservation = market_state.distributor_reservation_price

#         if decision.action == ActionType.ACCEPT:
#             # Only accept the original incoming offer if it meets all rules.
#             if (
#                 incoming_offer.price_per_unit < reservation
#                 or incoming_offer.price_per_unit <= 0
#                 or incoming_offer.quantity <= 0
#                 or incoming_offer.quantity > market_state.available_quantity
#                 or market_state.remaining_shelf_life_days
#                 < incoming_offer.minimum_remaining_shelf_life_days
#             ):
#                 return None
#             return Decision(
#                 action=ActionType.ACCEPT,
#                 offer=incoming_offer,
#                 reason=decision.reason or "AI accepted a valid offer.",
#             )

#         if decision.action == ActionType.REJECT:
#             return Decision(
#                 action=ActionType.REJECT,
#                 reason=decision.reason or "AI rejected the offer.",
#             )

#         if decision.action == ActionType.COUNTER:
#             counter = decision.offer
#             if counter is None:
#                 return None
#             if (
#                 counter.seller_id != self.agent_id
#                 or counter.buyer_id != incoming_offer.buyer_id
#                 or counter.price_per_unit < reservation
#                 or counter.price_per_unit <= 0
#                 or counter.quantity <= 0
#                 or counter.quantity > market_state.available_quantity
#                 or market_state.remaining_shelf_life_days
#                 < counter.minimum_remaining_shelf_life_days
#             ):
#                 return None
#             return Decision(
#                 action=ActionType.COUNTER,
#                 offer=counter,
#                 reason=decision.reason or "AI generated a valid counteroffer.",
#             )

#         return None


#     def get_ai_metrics(self) -> dict:
#         """Return a copy of AI observability counters."""
#         return dict(self.ai_metrics)
"""Distributor agent.

The distributor seeks a reasonable price and liquidation before expiry.
Deterministic business constraints take priority over optional LLM suggestions.
"""

import os
from typing import Optional

from agents.base_agent import BaseAgent
from ai_strategy.provider import LLMDecisionProvider
from ai_strategy.prompts import distributor_response_prompt
from models.schemas import ActionType, Decision, MarketState, Offer


class DistributorAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str = "distributor",
        ai_enabled: Optional[bool] = None,
    ):
        super().__init__(agent_id)

        if ai_enabled is None:
            value = os.getenv("AI_ENABLED", "false")
            ai_enabled = value.strip().lower() in {"1", "true", "yes", "on"}

        self.ai_enabled = ai_enabled
        self.ai_provider = LLMDecisionProvider(
            enabled=ai_enabled,
            timeout=45.0,
            max_ai_calls=10,
        )
        self.last_decision_source = "RULE"
        # Observability only; these counters do not change negotiation rules.
        self.ai_metrics = {
            "ai_attempts": 0,
            "ai_responses_received": 0,
            "ai_decisions_used": 0,
            "invalid_ai_responses": 0,
            "fallbacks": 0,
            "rule_based_decisions": 0,
        }

    def respond_to_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        """Apply hard rules first; consult AI only for genuine negotiation."""
        rule_decision = self._rule_based_response(offer, market_state)

        # Invalid offers and offers that already satisfy the seller's rules
        # have deterministic outcomes. AI must not override them.
        if rule_decision.action in {ActionType.ACCEPT, ActionType.REJECT}:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_decision

        if not self.ai_enabled:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_decision

        prompt = distributor_response_prompt(
            market_state=market_state,
            incoming_offer=offer,
        )
        if self.ai_enabled:
            self.ai_metrics["ai_attempts"] += 1
        decision = self.ai_provider.get_decision(
            prompt,
            fallback=lambda: rule_decision,
        )

        if self.ai_provider.last_source == "ai":
            self.ai_metrics["ai_responses_received"] += 1

        validated = self._validate_ai_decision(
            decision,
            offer,
            market_state,
        )
        if validated is None:
            if self.ai_provider.last_source == "ai":
                self.ai_metrics["invalid_ai_responses"] += 1
            self.last_decision_source = "FALLBACK"
            self.ai_metrics["fallbacks"] += 1
            return rule_decision

        self.last_decision_source = (
            "AI" if self.ai_provider.last_source == "ai" else "FALLBACK"
        )
        if self.last_decision_source == "AI":
            self.ai_metrics["ai_decisions_used"] += 1
        else:
            self.ai_metrics["fallbacks"] += 1
        return validated

    def _rule_based_response(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        """Return deterministic accept/reject/counter based on hard constraints."""
        reservation_price = market_state.distributor_reservation_price

        if offer.price_per_unit <= 0 or offer.quantity <= 0:
            return Decision(
                action=ActionType.REJECT,
                reason="Offer price and quantity must be positive.",
            )

        if offer.quantity > market_state.available_quantity:
            return Decision(
                action=ActionType.REJECT,
                reason="Offer quantity exceeds available inventory.",
            )

        if market_state.remaining_shelf_life_days < offer.minimum_remaining_shelf_life_days:
            return Decision(
                action=ActionType.REJECT,
                reason="Offer requires more shelf life than the inventory has.",
            )

        if offer.price_per_unit >= reservation_price:
            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Offer meets or exceeds distributor reservation price "
                    "and inventory/shelf-life constraints."
                ),
            )

        # Never counter below reservation price.
        counter_offer = Offer(
            buyer_id=offer.buyer_id,
            seller_id=self.agent_id,
            price_per_unit=round(reservation_price, 2),
            quantity=offer.quantity,
            minimum_remaining_shelf_life_days=(
                offer.minimum_remaining_shelf_life_days
            ),
        )
        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Offer is below reservation price; distributor counters "
                "at its reservation price."
            ),
        )

    def _validate_ai_decision(
        self,
        decision: Decision,
        incoming_offer: Offer,
        market_state: MarketState,
    ) -> Optional[Decision]:
        """Validate AI output; never let it bypass deterministic constraints."""
        reservation = market_state.distributor_reservation_price

        if decision.action == ActionType.ACCEPT:
            # Only accept the original incoming offer if it meets all rules.
            if (
                incoming_offer.price_per_unit < reservation
                or incoming_offer.price_per_unit <= 0
                or incoming_offer.quantity <= 0
                or incoming_offer.quantity > market_state.available_quantity
                or market_state.remaining_shelf_life_days
                < incoming_offer.minimum_remaining_shelf_life_days
            ):
                return None
            return Decision(
                action=ActionType.ACCEPT,
                offer=incoming_offer,
                reason=decision.reason or "AI accepted a valid offer.",
            )

        if decision.action == ActionType.REJECT:
            return Decision(
                action=ActionType.REJECT,
                reason=decision.reason or "AI rejected the offer.",
            )

        if decision.action == ActionType.COUNTER:
            counter = decision.offer
            if counter is None:
                return None
            if (
                counter.seller_id != self.agent_id
                or counter.buyer_id != incoming_offer.buyer_id
                or counter.price_per_unit < reservation
                or counter.price_per_unit <= 0
                or counter.quantity <= 0
                or counter.quantity > market_state.available_quantity
                or market_state.remaining_shelf_life_days
                < counter.minimum_remaining_shelf_life_days
            ):
                return None
            return Decision(
                action=ActionType.COUNTER,
                offer=counter,
                reason=decision.reason or "AI generated a valid counteroffer.",
            )

        return None


    def get_ai_metrics(self) -> dict:
        """Return a copy of AI observability counters."""
        return dict(self.ai_metrics)
