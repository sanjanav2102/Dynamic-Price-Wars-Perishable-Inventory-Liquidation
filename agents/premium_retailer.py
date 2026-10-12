# # """
# # Premium retailer agent.

# # The premium retailer has higher willingness to pay, limited storage,
# # fast sales velocity, and a preference for products with adequate shelf life.
# # AI decisions are optional and are validated before they can be used.
# # """

# # import os
# # from typing import Optional

# # from agents.base_agent import BaseAgent
# # from ai_strategy.provider import LLMDecisionProvider
# # from ai_strategy.prompts import (
# #     retailer_initial_offer_prompt,
# #     retailer_response_prompt,
# # )
# # from models.schemas import (
# #     MarketState,
# #     RetailerState,
# #     Offer,
# #     Decision,
# #     ActionType,
# # )


# # class PremiumRetailerAgent(BaseAgent):
# #     def __init__(
# #         self,
# #         state: RetailerState,
# #         ai_enabled: Optional[bool] = None,
# #     ):
# #         super().__init__(state.retailer_id)
# #         self.state = state

# #         if ai_enabled is None:
# #             value = os.getenv("AI_ENABLED", "false")
# #             ai_enabled = value.strip().lower() in {
# #                 "1", "true", "yes", "on"
# #             }

# #         self.ai_enabled = ai_enabled
# #         self.ai_provider = LLMDecisionProvider(
# #             enabled=ai_enabled,
# #             timeout=45.0,
# #             max_ai_calls=10,
# #         )
# #         self.last_decision_source = "RULE"

# #     def make_initial_offer(self, market_state: MarketState) -> Optional[Offer]:
# #         rule_offer = self._make_rule_based_initial_offer(market_state)

# #         # Resource exhaustion is a normal walk-away outcome, not an exception.
# #         if rule_offer is None:
# #             self.last_decision_source = "RULE"
# #             return None

# #         if not self.ai_enabled:
# #             self.last_decision_source = "RULE"
# #             return rule_offer

# #         fallback_decision = Decision(
# #             action=ActionType.COUNTER,
# #             offer=rule_offer,
# #             reason="Rule-based fallback initial offer.",
# #         )
# #         prompt = retailer_initial_offer_prompt(
# #             retailer_role="premium grocery retailer",
# #             market_state=market_state,
# #             retailer_state=self.state,
# #         )
# #         decision = self.ai_provider.get_decision(
# #             prompt,
# #             fallback=lambda: fallback_decision,
# #         )

# #         if (
# #             decision.offer is None
# #             or not self._is_valid_ai_offer(decision.offer, market_state)
# #         ):
# #             self.last_decision_source = "RULE"
# #             return rule_offer

# #         self.last_decision_source = (
# #             "AI" if self.ai_provider.last_source == "ai" else "FALLBACK"
# #         )
# #         return decision.offer

# #     def respond_to_offer(
# #         self,
# #         offer: Offer,
# #         market_state: MarketState,
# #     ) -> Decision:
# #         return self.respond_to_counter(offer, market_state)

    
# #     def respond_to_counter(
# #         self,
# #         offer: Offer,
# #         market_state: MarketState,
# #     ) -> Decision:
# #         """Use rules for decisive outcomes and AI for eligible counteroffers."""

# #         rule_decision = self._rule_based_response(offer, market_state)

# #         # Keep deterministic acceptance and hard-constraint walk-away decisions.
# #         if rule_decision.action in {
# #             ActionType.ACCEPT,
# #             ActionType.WALK_AWAY,
# #         }:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         # Use the rule-based counteroffer when AI is disabled.
# #         if not self.ai_enabled:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         prompt = retailer_response_prompt(
# #             retailer_role="premium grocery retailer",
# #             market_state=market_state,
# #             retailer_state=self.state,
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

# #         # Invalid AI output must never bypass deterministic safeguards.
# #         if validated is None:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         self.last_decision_source = (
# #             "AI"
# #             if self.ai_provider.last_source == "ai"
# #             else "FALLBACK"
# #         )

# #         return validated


    
# #     def _make_rule_based_initial_offer(
# #         self,
# #         market_state: MarketState,
# #     ) -> Optional[Offer]:
# #         reservation = market_state.distributor_reservation_price
# #         max_price = self.state.max_willingness_to_pay

# #         # No mutually acceptable price/resources means a graceful walk-away.
# #         if (
# #             reservation <= 0
# #             or max_price < reservation
# #             or self.state.budget < reservation
# #             or self.state.available_capacity <= 0
# #             or market_state.available_quantity <= 0
# #             or market_state.remaining_shelf_life_days
# #             < self.state.minimum_required_shelf_life_days
# #         ):
# #             return None

# #         price = round(reservation, 2)
# #         budget_quantity = int(self.state.budget // price)
# #         quantity = min(
# #             self.state.available_capacity,
# #             market_state.available_quantity,
# #             budget_quantity,
# #             max(1, int(self.state.sales_velocity_per_day * 2)),
# #             100,
# #         )

# #         if quantity <= 0:
# #             return None

# #         return Offer(
# #             buyer_id=self.state.retailer_id,
# #             seller_id="distributor",
# #             price_per_unit=price,
# #             quantity=quantity,
# #             minimum_remaining_shelf_life_days=(
# #                 self.state.minimum_required_shelf_life_days
# #             ),
# #         )


# #     def _rule_based_response(
# #         self,
# #         offer: Offer,
# #         market_state: MarketState,
# #     ) -> Decision:
# #         max_price = self.state.max_willingness_to_pay
# #         required_shelf_life = self.state.minimum_required_shelf_life_days

# #         # Invalid or impossible incoming offers cannot be accepted.
# #         if (
# #             offer.price_per_unit <= 0
# #             or offer.quantity <= 0
# #             or offer.quantity > market_state.available_quantity
# #             or market_state.remaining_shelf_life_days < required_shelf_life
# #             or offer.minimum_remaining_shelf_life_days > market_state.remaining_shelf_life_days
# #         ):
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason="Offer is invalid or does not meet inventory/shelf-life requirements.",
# #             )

# #         total_cost = offer.price_per_unit * offer.quantity
# #         if (
# #             offer.price_per_unit <= max_price
# #             and offer.quantity <= self.state.available_capacity
# #             and total_cost <= self.state.budget
# #             and offer.price_per_unit >= market_state.distributor_reservation_price
# #         ):
# #             return Decision(
# #                 action=ActionType.ACCEPT,
# #                 offer=offer,
# #                 reason=(
# #                     "Premium retailer accepts: price, budget, capacity, "
# #                     "inventory, and shelf-life constraints are satisfied."
# #                 ),
# #             )

# #         # A counteroffer must meet the seller's reservation price and
# #         # the retailer's maximum price. If no mutually acceptable price
# #         # exists, do not create a futile counteroffer.
# #         counter_price = min(
# #             max_price,
# #             max(
# #                 market_state.distributor_reservation_price,
# #                 (offer.price_per_unit + max_price) / 2,
# #             ),
# #         )
# #         counter_price = round(counter_price, 2)

# #         if counter_price <= 0 or counter_price < market_state.distributor_reservation_price:
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason="No price satisfies both the retailer and distributor.",
# #             )

# #         affordable_quantity = int(self.state.budget // counter_price)
# #         quantity = min(
# #             offer.quantity,
# #             max(0, self.state.available_capacity),
# #             max(0, market_state.available_quantity),
# #             max(0, affordable_quantity),
# #         )

# #         if quantity <= 0:
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason="No positive quantity fits the retailer's budget and capacity.",
# #             )

# #         counter_offer = Offer(
# #             buyer_id=self.state.retailer_id,
# #             seller_id="distributor",
# #             price_per_unit=counter_price,
# #             quantity=quantity,
# #             minimum_remaining_shelf_life_days=required_shelf_life,
# #         )
# #         return Decision(
# #             action=ActionType.COUNTER,
# #             offer=counter_offer,
# #             reason=(
# #                 "Premium retailer counters with a price and quantity that "
# #                 "fit its budget, capacity, and the distributor's reservation price."
# #             ),
# #         )

# #     def _is_valid_ai_offer(
# #         self,
# #         offer: Offer,
# #         market_state: MarketState,
# #     ) -> bool:
# #         return (
# #             offer.buyer_id == self.state.retailer_id
# #             and offer.seller_id == "distributor"
# #             and offer.quantity > 0
# #             and offer.quantity <= self.state.available_capacity
# #             and offer.quantity <= market_state.available_quantity
# #             and offer.price_per_unit > 0
# #             and offer.price_per_unit <= self.state.max_willingness_to_pay
# #             and offer.quantity * offer.price_per_unit <= self.state.budget
# #             and offer.minimum_remaining_shelf_life_days
# #                 >= self.state.minimum_required_shelf_life_days
# #             and market_state.remaining_shelf_life_days
# #                 >= offer.minimum_remaining_shelf_life_days
# #             and offer.price_per_unit
# #                 >= market_state.distributor_reservation_price
# #         )

# #     def _validate_ai_decision(
# #         self,
# #         decision: Decision,
# #         incoming_offer: Offer,
# #         market_state: MarketState,
# #     ) -> Optional[Decision]:
# #         if decision.action == ActionType.ACCEPT:
# #             # Accept the incoming offer only after validating every constraint.
# #             if (
# #                 incoming_offer.price_per_unit <= 0
# #                 or incoming_offer.quantity <= 0
# #                 or incoming_offer.price_per_unit > self.state.max_willingness_to_pay
# #                 or incoming_offer.quantity > self.state.available_capacity
# #                 or incoming_offer.quantity > market_state.available_quantity
# #                 or incoming_offer.quantity * incoming_offer.price_per_unit > self.state.budget
# #                 or incoming_offer.price_per_unit < market_state.distributor_reservation_price
# #                 or market_state.remaining_shelf_life_days
# #                     < self.state.minimum_required_shelf_life_days
# #                 or incoming_offer.minimum_remaining_shelf_life_days
# #                     < self.state.minimum_required_shelf_life_days
# #                 or market_state.remaining_shelf_life_days
# #                     < incoming_offer.minimum_remaining_shelf_life_days
# #             ):
# #                 return None

# #             return Decision(
# #                 action=ActionType.ACCEPT,
# #                 offer=incoming_offer,
# #                 reason=decision.reason or "AI accepted a valid, affordable offer.",
# #             )

# #         if decision.action == ActionType.WALK_AWAY:
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason=decision.reason or "AI walked away.",
# #             )

# #         if decision.action == ActionType.COUNTER:
# #             if decision.offer is None:
# #                 return None
# #             if not self._is_valid_ai_offer(decision.offer, market_state):
# #                 return None
# #             return Decision(
# #                 action=ActionType.COUNTER,
# #                 offer=decision.offer,
# #                 reason=decision.reason or "AI generated a valid counteroffer.",
# #             )

# #         return None
# """
# Premium retailer agent.

# The premium retailer has higher willingness to pay, limited storage,
# fast sales velocity, and a preference for products with adequate shelf life.
# AI decisions are optional and are validated before they can be used.
# """

# import os
# from typing import Optional

# from agents.base_agent import BaseAgent
# from ai_strategy.provider import LLMDecisionProvider
# from ai_strategy.prompts import (
#     retailer_initial_offer_prompt,
#     retailer_response_prompt,
# )
# from models.schemas import (
#     MarketState,
#     RetailerState,
#     Offer,
#     Decision,
#     ActionType,
# )


# class PremiumRetailerAgent(BaseAgent):
#     def __init__(
#         self,
#         state: RetailerState,
#         ai_enabled: Optional[bool] = None,
#     ):
#         super().__init__(state.retailer_id)
#         self.state = state

#         if ai_enabled is None:
#             value = os.getenv("AI_ENABLED", "false")
#             ai_enabled = value.strip().lower() in {
#                 "1", "true", "yes", "on"
#             }

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

#     def make_initial_offer(self, market_state: MarketState) -> Optional[Offer]:
#         rule_offer = self._make_rule_based_initial_offer(market_state)

#         # Resource exhaustion is a normal walk-away outcome, not an exception.
#         if rule_offer is None:
#             self.last_decision_source = "RULE"
#             return None

#         if not self.ai_enabled:
#             self.last_decision_source = "RULE"
#             return rule_offer

#         fallback_decision = Decision(
#             action=ActionType.COUNTER,
#             offer=rule_offer,
#             reason="Rule-based fallback initial offer.",
#         )
#         prompt = retailer_initial_offer_prompt(
#             retailer_role="premium grocery retailer",
#             market_state=market_state,
#             retailer_state=self.state,
#         )
#         if self.ai_enabled:
#             self.ai_metrics["ai_attempts"] += 1
#         decision = self.ai_provider.get_decision(
#             prompt,
#             fallback=lambda: fallback_decision,
#         )

#         if self.ai_provider.last_source == "ai":
#             self.ai_metrics["ai_responses_received"] += 1
#         elif self.ai_provider.last_source == "fallback":
#             self.ai_metrics["fallbacks"] += 1

#         if (
#             decision.offer is None
#             or not self._is_valid_ai_offer(decision.offer, market_state)
#         ):
#             self.last_decision_source = "RULE"
#             return rule_offer

#         self.last_decision_source = (
#             "AI" if self.ai_provider.last_source == "ai" else "FALLBACK"
#         )
#         if self.last_decision_source == "AI":
#             self.ai_metrics["ai_decisions_used"] += 1
#         elif self.ai_provider.last_source == "fallback":
#             self.ai_metrics["fallbacks"] += 1
#         return decision.offer

#     def respond_to_offer(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         return self.respond_to_counter(offer, market_state)

    
#     def respond_to_counter(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         """Use rules for decisive outcomes and AI for eligible counteroffers."""

#         rule_decision = self._rule_based_response(offer, market_state)

#         # Keep deterministic acceptance and hard-constraint walk-away decisions.
#         if rule_decision.action in {
#             ActionType.ACCEPT,
#             ActionType.WALK_AWAY,
#         }:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         # Use the rule-based counteroffer when AI is disabled.
#         if not self.ai_enabled:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         prompt = retailer_response_prompt(
#             retailer_role="premium grocery retailer",
#             market_state=market_state,
#             retailer_state=self.state,
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

#         # Invalid AI output must never bypass deterministic safeguards.
#         if validated is None:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         self.last_decision_source = (
#             "AI"
#             if self.ai_provider.last_source == "ai"
#             else "FALLBACK"
#         )
#         if self.last_decision_source == "AI":
#             self.ai_metrics["ai_decisions_used"] += 1
#         elif self.ai_provider.last_source == "fallback":
#             self.ai_metrics["fallbacks"] += 1

#         return validated


    
#     def _make_rule_based_initial_offer(
#         self,
#         market_state: MarketState,
#     ) -> Optional[Offer]:
#         reservation = market_state.distributor_reservation_price
#         max_price = self.state.max_willingness_to_pay

#         # No mutually acceptable price/resources means a graceful walk-away.
#         if (
#             reservation <= 0
#             or max_price < reservation
#             or self.state.budget < reservation
#             or self.state.available_capacity <= 0
#             or market_state.available_quantity <= 0
#             or market_state.remaining_shelf_life_days
#             < self.state.minimum_required_shelf_life_days
#         ):
#             return None

#         price = round(reservation, 2)
#         budget_quantity = int(self.state.budget // price)
#         quantity = min(
#             self.state.available_capacity,
#             market_state.available_quantity,
#             budget_quantity,
#             max(1, int(self.state.sales_velocity_per_day * 2)),
#             100,
#         )

#         if quantity <= 0:
#             return None

#         return Offer(
#             buyer_id=self.state.retailer_id,
#             seller_id="distributor",
#             price_per_unit=price,
#             quantity=quantity,
#             minimum_remaining_shelf_life_days=(
#                 self.state.minimum_required_shelf_life_days
#             ),
#         )


#     def _rule_based_response(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         max_price = self.state.max_willingness_to_pay
#         required_shelf_life = self.state.minimum_required_shelf_life_days

#         # Invalid or impossible incoming offers cannot be accepted.
#         if (
#             offer.price_per_unit <= 0
#             or offer.quantity <= 0
#             or offer.quantity > market_state.available_quantity
#             or market_state.remaining_shelf_life_days < required_shelf_life
#             or offer.minimum_remaining_shelf_life_days > market_state.remaining_shelf_life_days
#         ):
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason="Offer is invalid or does not meet inventory/shelf-life requirements.",
#             )

#         total_cost = offer.price_per_unit * offer.quantity
#         if (
#             offer.price_per_unit <= max_price
#             and offer.quantity <= self.state.available_capacity
#             and total_cost <= self.state.budget
#             and offer.price_per_unit >= market_state.distributor_reservation_price
#         ):
#             return Decision(
#                 action=ActionType.ACCEPT,
#                 offer=offer,
#                 reason=(
#                     "Premium retailer accepts: price, budget, capacity, "
#                     "inventory, and shelf-life constraints are satisfied."
#                 ),
#             )

#         # A counteroffer must meet the seller's reservation price and
#         # the retailer's maximum price. If no mutually acceptable price
#         # exists, do not create a futile counteroffer.
#         counter_price = min(
#             max_price,
#             max(
#                 market_state.distributor_reservation_price,
#                 (offer.price_per_unit + max_price) / 2,
#             ),
#         )
#         counter_price = round(counter_price, 2)

#         if counter_price <= 0 or counter_price < market_state.distributor_reservation_price:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason="No price satisfies both the retailer and distributor.",
#             )

#         affordable_quantity = int(self.state.budget // counter_price)
#         quantity = min(
#             offer.quantity,
#             max(0, self.state.available_capacity),
#             max(0, market_state.available_quantity),
#             max(0, affordable_quantity),
#         )

#         if quantity <= 0:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason="No positive quantity fits the retailer's budget and capacity.",
#             )

#         counter_offer = Offer(
#             buyer_id=self.state.retailer_id,
#             seller_id="distributor",
#             price_per_unit=counter_price,
#             quantity=quantity,
#             minimum_remaining_shelf_life_days=required_shelf_life,
#         )
#         return Decision(
#             action=ActionType.COUNTER,
#             offer=counter_offer,
#             reason=(
#                 "Premium retailer counters with a price and quantity that "
#                 "fit its budget, capacity, and the distributor's reservation price."
#             ),
#         )

#     def _is_valid_ai_offer(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> bool:
#         return (
#             offer.buyer_id == self.state.retailer_id
#             and offer.seller_id == "distributor"
#             and offer.quantity > 0
#             and offer.quantity <= self.state.available_capacity
#             and offer.quantity <= market_state.available_quantity
#             and offer.price_per_unit > 0
#             and offer.price_per_unit <= self.state.max_willingness_to_pay
#             and offer.quantity * offer.price_per_unit <= self.state.budget
#             and offer.minimum_remaining_shelf_life_days
#                 >= self.state.minimum_required_shelf_life_days
#             and market_state.remaining_shelf_life_days
#                 >= offer.minimum_remaining_shelf_life_days
#             and offer.price_per_unit
#                 >= market_state.distributor_reservation_price
#         )

#     def _validate_ai_decision(
#         self,
#         decision: Decision,
#         incoming_offer: Offer,
#         market_state: MarketState,
#     ) -> Optional[Decision]:
#         if decision.action == ActionType.ACCEPT:
#             # Accept the incoming offer only after validating every constraint.
#             if (
#                 incoming_offer.price_per_unit <= 0
#                 or incoming_offer.quantity <= 0
#                 or incoming_offer.price_per_unit > self.state.max_willingness_to_pay
#                 or incoming_offer.quantity > self.state.available_capacity
#                 or incoming_offer.quantity > market_state.available_quantity
#                 or incoming_offer.quantity * incoming_offer.price_per_unit > self.state.budget
#                 or incoming_offer.price_per_unit < market_state.distributor_reservation_price
#                 or market_state.remaining_shelf_life_days
#                     < self.state.minimum_required_shelf_life_days
#                 or incoming_offer.minimum_remaining_shelf_life_days
#                     < self.state.minimum_required_shelf_life_days
#                 or market_state.remaining_shelf_life_days
#                     < incoming_offer.minimum_remaining_shelf_life_days
#             ):
#                 return None

#             return Decision(
#                 action=ActionType.ACCEPT,
#                 offer=incoming_offer,
#                 reason=decision.reason or "AI accepted a valid, affordable offer.",
#             )

#         if decision.action == ActionType.WALK_AWAY:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason=decision.reason or "AI walked away.",
#             )

#         if decision.action == ActionType.COUNTER:
#             if decision.offer is None:
#                 return None
#             if not self._is_valid_ai_offer(decision.offer, market_state):
#                 return None
#             return Decision(
#                 action=ActionType.COUNTER,
#                 offer=decision.offer,
#                 reason=decision.reason or "AI generated a valid counteroffer.",
#             )

#         return None


#     def get_ai_metrics(self) -> dict:
#         """Return a copy of AI observability counters."""
#         return dict(self.ai_metrics)
"""
Premium retailer agent.

The premium retailer has higher willingness to pay, limited storage,
fast sales velocity, and a preference for products with adequate shelf life.
AI decisions are optional and are validated before they can be used.
"""

import os
from typing import Optional

from agents.base_agent import BaseAgent
from ai_strategy.provider import LLMDecisionProvider
from ai_strategy.prompts import (
    retailer_initial_offer_prompt,
    retailer_response_prompt,
)
from models.schemas import (
    MarketState,
    RetailerState,
    Offer,
    Decision,
    ActionType,
)


class PremiumRetailerAgent(BaseAgent):
    def __init__(
        self,
        state: RetailerState,
        ai_enabled: Optional[bool] = None,
    ):
        super().__init__(state.retailer_id)
        self.state = state

        if ai_enabled is None:
            value = os.getenv("AI_ENABLED", "false")
            ai_enabled = value.strip().lower() in {
                "1", "true", "yes", "on"
            }

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

    def make_initial_offer(self, market_state: MarketState) -> Optional[Offer]:
        rule_offer = self._make_rule_based_initial_offer(market_state)

        # Resource exhaustion is a normal walk-away outcome, not an exception.
        if rule_offer is None:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return None

        if not self.ai_enabled:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_offer

        fallback_decision = Decision(
            action=ActionType.COUNTER,
            offer=rule_offer,
            reason="Rule-based fallback initial offer.",
        )
        prompt = retailer_initial_offer_prompt(
            retailer_role="premium grocery retailer",
            market_state=market_state,
            retailer_state=self.state,
        )
        if self.ai_enabled:
            self.ai_metrics["ai_attempts"] += 1
        decision = self.ai_provider.get_decision(
            prompt,
            fallback=lambda: fallback_decision,
        )

        if self.ai_provider.last_source == "ai":
            self.ai_metrics["ai_responses_received"] += 1

        if (
            decision.offer is None
            or not self._is_valid_ai_offer(decision.offer, market_state)
        ):
            if self.ai_provider.last_source == "ai":
                self.ai_metrics["invalid_ai_responses"] += 1
            self.last_decision_source = "FALLBACK"
            self.ai_metrics["fallbacks"] += 1
            return rule_offer

        self.last_decision_source = (
            "AI" if self.ai_provider.last_source == "ai" else "FALLBACK"
        )
        if self.last_decision_source == "AI":
            self.ai_metrics["ai_decisions_used"] += 1
        else:
            self.ai_metrics["fallbacks"] += 1
        return decision.offer

    def respond_to_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        return self.respond_to_counter(offer, market_state)

    
    def respond_to_counter(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        """Use rules for decisive outcomes and AI for eligible counteroffers."""

        rule_decision = self._rule_based_response(offer, market_state)

        # Keep deterministic acceptance and hard-constraint walk-away decisions.
        if rule_decision.action in {
            ActionType.ACCEPT,
            ActionType.WALK_AWAY,
        }:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_decision

        # Use the rule-based counteroffer when AI is disabled.
        if not self.ai_enabled:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_decision

        prompt = retailer_response_prompt(
            retailer_role="premium grocery retailer",
            market_state=market_state,
            retailer_state=self.state,
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

        # Invalid AI output must never bypass deterministic safeguards.
        if validated is None:
            if self.ai_provider.last_source == "ai":
                self.ai_metrics["invalid_ai_responses"] += 1
            self.last_decision_source = "FALLBACK"
            self.ai_metrics["fallbacks"] += 1
            return rule_decision

        self.last_decision_source = (
            "AI"
            if self.ai_provider.last_source == "ai"
            else "FALLBACK"
        )
        if self.last_decision_source == "AI":
            self.ai_metrics["ai_decisions_used"] += 1
        else:
            self.ai_metrics["fallbacks"] += 1

        return validated


    
    def _make_rule_based_initial_offer(
        self,
        market_state: MarketState,
    ) -> Optional[Offer]:
        reservation = market_state.distributor_reservation_price
        max_price = self.state.max_willingness_to_pay

        # No mutually acceptable price/resources means a graceful walk-away.
        if (
            reservation <= 0
            or max_price < reservation
            or self.state.budget < reservation
            or self.state.available_capacity <= 0
            or market_state.available_quantity <= 0
            or market_state.remaining_shelf_life_days
            < self.state.minimum_required_shelf_life_days
        ):
            return None

        price = round(reservation, 2)
        budget_quantity = int(self.state.budget // price)
        quantity = min(
            self.state.available_capacity,
            market_state.available_quantity,
            budget_quantity,
            max(1, int(self.state.sales_velocity_per_day * 2)),
            100,
        )

        if quantity <= 0:
            return None

        return Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=price,
            quantity=quantity,
            minimum_remaining_shelf_life_days=(
                self.state.minimum_required_shelf_life_days
            ),
        )


    def _rule_based_response(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        max_price = self.state.max_willingness_to_pay
        required_shelf_life = self.state.minimum_required_shelf_life_days

        # Invalid or impossible incoming offers cannot be accepted.
        if (
            offer.price_per_unit <= 0
            or offer.quantity <= 0
            or offer.quantity > market_state.available_quantity
            or market_state.remaining_shelf_life_days < required_shelf_life
            or offer.minimum_remaining_shelf_life_days > market_state.remaining_shelf_life_days
        ):
            return Decision(
                action=ActionType.WALK_AWAY,
                reason="Offer is invalid or does not meet inventory/shelf-life requirements.",
            )

        total_cost = offer.price_per_unit * offer.quantity
        if (
            offer.price_per_unit <= max_price
            and offer.quantity <= self.state.available_capacity
            and total_cost <= self.state.budget
            and offer.price_per_unit >= market_state.distributor_reservation_price
        ):
            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Premium retailer accepts: price, budget, capacity, "
                    "inventory, and shelf-life constraints are satisfied."
                ),
            )

        # A counteroffer must meet the seller's reservation price and
        # the retailer's maximum price. If no mutually acceptable price
        # exists, do not create a futile counteroffer.
        counter_price = min(
            max_price,
            max(
                market_state.distributor_reservation_price,
                (offer.price_per_unit + max_price) / 2,
            ),
        )
        counter_price = round(counter_price, 2)

        if counter_price <= 0 or counter_price < market_state.distributor_reservation_price:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason="No price satisfies both the retailer and distributor.",
            )

        affordable_quantity = int(self.state.budget // counter_price)
        quantity = min(
            offer.quantity,
            max(0, self.state.available_capacity),
            max(0, market_state.available_quantity),
            max(0, affordable_quantity),
        )

        if quantity <= 0:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason="No positive quantity fits the retailer's budget and capacity.",
            )

        counter_offer = Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=counter_price,
            quantity=quantity,
            minimum_remaining_shelf_life_days=required_shelf_life,
        )
        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Premium retailer counters with a price and quantity that "
                "fit its budget, capacity, and the distributor's reservation price."
            ),
        )

    def _is_valid_ai_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> bool:
        return (
            offer.buyer_id == self.state.retailer_id
            and offer.seller_id == "distributor"
            and offer.quantity > 0
            and offer.quantity <= self.state.available_capacity
            and offer.quantity <= market_state.available_quantity
            and offer.price_per_unit > 0
            and offer.price_per_unit <= self.state.max_willingness_to_pay
            and offer.quantity * offer.price_per_unit <= self.state.budget
            and offer.minimum_remaining_shelf_life_days
                >= self.state.minimum_required_shelf_life_days
            and market_state.remaining_shelf_life_days
                >= offer.minimum_remaining_shelf_life_days
            and offer.price_per_unit
                >= market_state.distributor_reservation_price
        )

    def _validate_ai_decision(
        self,
        decision: Decision,
        incoming_offer: Offer,
        market_state: MarketState,
    ) -> Optional[Decision]:
        if decision.action == ActionType.ACCEPT:
            # Accept the incoming offer only after validating every constraint.
            if (
                incoming_offer.price_per_unit <= 0
                or incoming_offer.quantity <= 0
                or incoming_offer.price_per_unit > self.state.max_willingness_to_pay
                or incoming_offer.quantity > self.state.available_capacity
                or incoming_offer.quantity > market_state.available_quantity
                or incoming_offer.quantity * incoming_offer.price_per_unit > self.state.budget
                or incoming_offer.price_per_unit < market_state.distributor_reservation_price
                or market_state.remaining_shelf_life_days
                    < self.state.minimum_required_shelf_life_days
                or incoming_offer.minimum_remaining_shelf_life_days
                    < self.state.minimum_required_shelf_life_days
                or market_state.remaining_shelf_life_days
                    < incoming_offer.minimum_remaining_shelf_life_days
            ):
                return None

            return Decision(
                action=ActionType.ACCEPT,
                offer=incoming_offer,
                reason=decision.reason or "AI accepted a valid, affordable offer.",
            )

        if decision.action == ActionType.WALK_AWAY:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason=decision.reason or "AI walked away.",
            )

        if decision.action == ActionType.COUNTER:
            if decision.offer is None:
                return None
            if not self._is_valid_ai_offer(decision.offer, market_state):
                return None
            return Decision(
                action=ActionType.COUNTER,
                offer=decision.offer,
                reason=decision.reason or "AI generated a valid counteroffer.",
            )

        return None


    def get_ai_metrics(self) -> dict:
        """Return a copy of AI observability counters."""
        return dict(self.ai_metrics)
