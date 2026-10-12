
# # """Budget retailer agent.

# # The budget retailer is price-sensitive and may purchase larger quantities.
# # AI decisions are optional; hard budget, capacity, inventory, and freshness
# # constraints are validated in Python.
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


# # class BudgetRetailerAgent(BaseAgent):
# #     MAX_DEAL_QUANTITY = 100
# #     def __init__(
# #         self,
# #         state: RetailerState,
# #         ai_enabled: Optional[bool] = None,
# #     ):
# #         super().__init__(state.retailer_id)
# #         self.state = state

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

# #     def make_initial_offer(self, market_state: MarketState) -> Optional[Offer]:
# #         """Create a valid opening offer, falling back safely if resources are exhausted."""
# #         rule_offer = self._make_rule_based_initial_offer(market_state)

# #         # Do not construct an AI fallback around an impossible opening offer.
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
# #             retailer_role="budget grocery retailer",
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
# #         """Respond safely, using AI for eligible counteroffer decisions."""

# #         rule_decision = self._rule_based_response(offer, market_state)

# #         # Preserve deterministic decisions for acceptance and hard constraints.
# #         if rule_decision.action in {
# #             ActionType.ACCEPT,
# #             ActionType.WALK_AWAY,
# #         }:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         # If AI is disabled, use the deterministic counteroffer.
# #         if not self.ai_enabled:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         prompt = retailer_response_prompt(
# #             retailer_role="budget grocery retailer",
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

# #         # Reject invalid AI output and safely fall back to the rule decision.
# #         if validated is None:
# #             self.last_decision_source = "RULE"
# #             return rule_decision

# #         # Report whether the provider actually supplied the decision.
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
# #         """Build a feasible opening bid, or return None to walk away safely."""
# #         reservation = market_state.distributor_reservation_price
# #         max_price = self.state.max_willingness_to_pay

# #         # The opening bid may be below reservation, but it must be feasible
# #         # for the retailer's actual resources.
# #         if (
# #             reservation <= 0
# #             or max_price <= 0
# #             or self.state.budget <= 0
# #             or self.state.available_capacity <= 0
# #             or market_state.available_quantity <= 0
# #             or market_state.remaining_shelf_life_days
# #             < self.state.minimum_required_shelf_life_days
# #         ):
# #             return None

# #         price = round(min(max_price, reservation * 0.80), 2)
# #         if price <= 0:
# #             return None

# #         affordable_quantity = int(self.state.budget // price)
# #         desired_quantity = max(1, int(self.state.sales_velocity_per_day * 2))
        
# #         # Opening offers express the retailer's two-day demand target.
# #         # The deal limit is enforced when a deal is validated/executed.
# #         quantity = min(
# #             self.state.available_capacity,
# #             market_state.available_quantity,
# #             affordable_quantity,
# #             desired_quantity,
# #         )

# #         if quantity <= 0:
# #             return None

# #         return Offer(
# #             buyer_id=self.state.retailer_id,
# #             seller_id="distributor",
# #             price_per_unit=round(max(0.01, price), 2),
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
# #         """Accept valid offers; otherwise make a safe, affordable counteroffer."""
# #         max_price = self.state.max_willingness_to_pay
# #         required_shelf_life = self.state.minimum_required_shelf_life_days
# #         reservation_price = market_state.distributor_reservation_price

# #         # Reject invalid offers or situations where a purchase is impossible.
# #         if (
# #             offer.price_per_unit <= 0
# #             or offer.quantity <= 0
# #             or market_state.available_quantity <= 0
# #             or self.state.available_capacity <= 0
# #             or self.state.budget <= 0
# #             or market_state.remaining_shelf_life_days < required_shelf_life
# #             or offer.minimum_remaining_shelf_life_days < required_shelf_life
# #             or market_state.remaining_shelf_life_days
# #             < offer.minimum_remaining_shelf_life_days
# #         ):
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason=(
# #                     "Offer is invalid or fails budget, capacity, inventory, "
# #                     "or freshness requirements."
# #                 ),
# #             )

# #         # Accept only when all business constraints are satisfied.
# #         total_cost = offer.price_per_unit * offer.quantity
# #         if (
# #             offer.price_per_unit >= reservation_price
# #             and offer.quantity <= self.MAX_DEAL_QUANTITY
# #             and offer.price_per_unit <= max_price
# #             and offer.quantity <= self.state.available_capacity
# #             and offer.quantity <= market_state.available_quantity
# #             and total_cost <= self.state.budget
# #         ):
# #             return Decision(
# #                 action=ActionType.ACCEPT,
# #                 offer=offer,
# #                 reason=(
# #                     "Budget retailer accepts: price, budget, capacity, "
# #                     "inventory, and freshness checks passed."
# #                 ),
# #             )

# #         # Walk away when there is no overlap between the buyer's maximum
# #         # price and the distributor's minimum acceptable price.
# #         if reservation_price <= 0 or max_price < reservation_price:
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason="No mutually acceptable positive price exists.",
# #             )

# #         # Aim for a compromise between the incoming price and the
# #         # retailer's maximum willingness to pay, while respecting the
# #         # distributor's reservation price.
# #         target_price = (offer.price_per_unit + max_price) / 2

# #         counter_price = round(
# #             max(
# #                 reservation_price,
# #                 min(max_price, target_price),
# #             ),
# #             2,
# #         )

# #         if (
# #             counter_price <= 0
# #             or counter_price < reservation_price
# #             or counter_price > max_price
# #         ):
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason="No valid counteroffer price is available.",
# #             )

# #         # Calculate the maximum quantity the retailer can afford.
# #         affordable_quantity = int(self.state.budget // counter_price)
# #         counter_quantity = min(
# #             offer.quantity,
# #             self.MAX_DEAL_QUANTITY,
# #             max(0, self.state.available_capacity),
# #             max(0, market_state.available_quantity),
# #             max(0, affordable_quantity),
# #         )

# #         if counter_quantity <= 0:
# #             return Decision(
# #                 action=ActionType.WALK_AWAY,
# #                 reason=(
# #                     "Budget retailer cannot afford any units "
# #                     "at a mutually acceptable price."
# #                 ),
# #             )

# #         counter_offer = Offer(
# #             buyer_id=self.state.retailer_id,
# #             seller_id="distributor",
# #             price_per_unit=counter_price,
# #             quantity=counter_quantity,
# #             minimum_remaining_shelf_life_days=required_shelf_life,
# #         )

# #         return Decision(
# #             action=ActionType.COUNTER,
# #             offer=counter_offer,
# #             reason=(
# #                 "Budget retailer proposes a compromise price and an "
# #                 "affordable quantity while respecting budget, capacity, "
# #                 "inventory, and freshness constraints."
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
# #             and offer.quantity <= self.MAX_DEAL_QUANTITY
# #             and offer.quantity <= self.state.available_capacity
# #             and offer.quantity <= market_state.available_quantity
# #             and offer.price_per_unit > 0
# #             and offer.price_per_unit <= self.state.max_willingness_to_pay
# #             # Initial offers may intentionally be below reservation price.
# #             and offer.quantity * offer.price_per_unit <= self.state.budget
# #             and offer.minimum_remaining_shelf_life_days
# #             >= self.state.minimum_required_shelf_life_days
# #             and market_state.remaining_shelf_life_days
# #             >= offer.minimum_remaining_shelf_life_days
# #         )

# #     def _validate_ai_decision(
# #         self,
# #         decision: Decision,
# #         incoming_offer: Offer,
# #         market_state: MarketState,
# #     ) -> Optional[Decision]:
# #         if decision.action == ActionType.ACCEPT:
# #             if (
# #                 incoming_offer.buyer_id != self.state.retailer_id
# #                 or incoming_offer.seller_id != "distributor"
# #                 or incoming_offer.quantity > self.MAX_DEAL_QUANTITY
# #                 or incoming_offer.price_per_unit <= 0
# #                 or incoming_offer.quantity <= 0
# #                 or incoming_offer.price_per_unit
# #                 > self.state.max_willingness_to_pay
# #                 or incoming_offer.price_per_unit
# #                 < market_state.distributor_reservation_price
# #                 or incoming_offer.quantity > self.state.available_capacity
# #                 or incoming_offer.quantity > market_state.available_quantity
# #                 or incoming_offer.quantity * incoming_offer.price_per_unit
# #                 > self.state.budget
# #                 or market_state.remaining_shelf_life_days
# #                 < self.state.minimum_required_shelf_life_days
# #                 or incoming_offer.minimum_remaining_shelf_life_days
# #                 < self.state.minimum_required_shelf_life_days
# #                 or market_state.remaining_shelf_life_days
# #                 < incoming_offer.minimum_remaining_shelf_life_days
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
# #             if decision.offer.quantity > self.MAX_DEAL_QUANTITY:
# #                 return None
# #             if not self._is_valid_ai_offer(decision.offer, market_state):
# #                 return None
# #             return Decision(
# #                 action=ActionType.COUNTER,
# #                 offer=decision.offer,
# #                 reason=decision.reason or "AI generated a valid counteroffer.",
# #             )

# #         return None

# """Budget retailer agent.

# The budget retailer is price-sensitive and may purchase larger quantities.
# AI decisions are optional; hard budget, capacity, inventory, and freshness
# constraints are validated in Python.
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


# class BudgetRetailerAgent(BaseAgent):
#     MAX_DEAL_QUANTITY = 100
#     def __init__(
#         self,
#         state: RetailerState,
#         ai_enabled: Optional[bool] = None,
#     ):
#         super().__init__(state.retailer_id)
#         self.state = state

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

#     def make_initial_offer(self, market_state: MarketState) -> Optional[Offer]:
#         """Create a valid opening offer, falling back safely if resources are exhausted."""
#         rule_offer = self._make_rule_based_initial_offer(market_state)

#         # Do not construct an AI fallback around an impossible opening offer.
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
#             retailer_role="budget grocery retailer",
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
#         """Respond safely, using AI for eligible counteroffer decisions."""

#         rule_decision = self._rule_based_response(offer, market_state)

#         # Preserve deterministic decisions for acceptance and hard constraints.
#         if rule_decision.action in {
#             ActionType.ACCEPT,
#             ActionType.WALK_AWAY,
#         }:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         # If AI is disabled, use the deterministic counteroffer.
#         if not self.ai_enabled:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         prompt = retailer_response_prompt(
#             retailer_role="budget grocery retailer",
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

#         # Reject invalid AI output and safely fall back to the rule decision.
#         if validated is None:
#             self.last_decision_source = "RULE"
#             return rule_decision

#         # Report whether the provider actually supplied the decision.
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
#         """Build a feasible opening bid, or return None to walk away safely."""
#         reservation = market_state.distributor_reservation_price
#         max_price = self.state.max_willingness_to_pay

#         # The opening bid may be below reservation, but it must be feasible
#         # for the retailer's actual resources.
#         if (
#             reservation <= 0
#             or max_price <= 0
#             or self.state.budget <= 0
#             or self.state.available_capacity <= 0
#             or market_state.available_quantity <= 0
#             or market_state.remaining_shelf_life_days
#             < self.state.minimum_required_shelf_life_days
#         ):
#             return None

#         price = round(min(max_price, reservation * 0.80), 2)
#         if price <= 0:
#             return None

#         affordable_quantity = int(self.state.budget // price)
#         desired_quantity = max(1, int(self.state.sales_velocity_per_day * 2))
        
#         # Opening offers express the retailer's two-day demand target.
#         # The deal limit is enforced when a deal is validated/executed.
#         quantity = min(
#             self.state.available_capacity,
#             market_state.available_quantity,
#             affordable_quantity,
#             desired_quantity,
#         )

#         if quantity <= 0:
#             return None

#         return Offer(
#             buyer_id=self.state.retailer_id,
#             seller_id="distributor",
#             price_per_unit=round(max(0.01, price), 2),
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
#         """Accept valid offers; otherwise make a safe, affordable counteroffer."""
#         max_price = self.state.max_willingness_to_pay
#         required_shelf_life = self.state.minimum_required_shelf_life_days
#         reservation_price = market_state.distributor_reservation_price

#         # Reject invalid offers or situations where a purchase is impossible.
#         if (
#             offer.price_per_unit <= 0
#             or offer.quantity <= 0
#             or market_state.available_quantity <= 0
#             or self.state.available_capacity <= 0
#             or self.state.budget <= 0
#             or market_state.remaining_shelf_life_days < required_shelf_life
#             or offer.minimum_remaining_shelf_life_days < required_shelf_life
#             or market_state.remaining_shelf_life_days
#             < offer.minimum_remaining_shelf_life_days
#         ):
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason=(
#                     "Offer is invalid or fails budget, capacity, inventory, "
#                     "or freshness requirements."
#                 ),
#             )

#         # Accept only when all business constraints are satisfied.
#         total_cost = offer.price_per_unit * offer.quantity
#         if (
#             offer.price_per_unit >= reservation_price
#             and offer.quantity <= self.MAX_DEAL_QUANTITY
#             and offer.price_per_unit <= max_price
#             and offer.quantity <= self.state.available_capacity
#             and offer.quantity <= market_state.available_quantity
#             and total_cost <= self.state.budget
#         ):
#             return Decision(
#                 action=ActionType.ACCEPT,
#                 offer=offer,
#                 reason=(
#                     "Budget retailer accepts: price, budget, capacity, "
#                     "inventory, and freshness checks passed."
#                 ),
#             )

#         # Walk away when there is no overlap between the buyer's maximum
#         # price and the distributor's minimum acceptable price.
#         if reservation_price <= 0 or max_price < reservation_price:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason="No mutually acceptable positive price exists.",
#             )

#         # Aim for a compromise between the incoming price and the
#         # retailer's maximum willingness to pay, while respecting the
#         # distributor's reservation price.
#         target_price = (offer.price_per_unit + max_price) / 2

#         counter_price = round(
#             max(
#                 reservation_price,
#                 min(max_price, target_price),
#             ),
#             2,
#         )

#         if (
#             counter_price <= 0
#             or counter_price < reservation_price
#             or counter_price > max_price
#         ):
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason="No valid counteroffer price is available.",
#             )

#         # Calculate the maximum quantity the retailer can afford.
#         affordable_quantity = int(self.state.budget // counter_price)
#         counter_quantity = min(
#             offer.quantity,
#             self.MAX_DEAL_QUANTITY,
#             max(0, self.state.available_capacity),
#             max(0, market_state.available_quantity),
#             max(0, affordable_quantity),
#         )

#         if counter_quantity <= 0:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason=(
#                     "Budget retailer cannot afford any units "
#                     "at a mutually acceptable price."
#                 ),
#             )

#         counter_offer = Offer(
#             buyer_id=self.state.retailer_id,
#             seller_id="distributor",
#             price_per_unit=counter_price,
#             quantity=counter_quantity,
#             minimum_remaining_shelf_life_days=required_shelf_life,
#         )

#         return Decision(
#             action=ActionType.COUNTER,
#             offer=counter_offer,
#             reason=(
#                 "Budget retailer proposes a compromise price and an "
#                 "affordable quantity while respecting budget, capacity, "
#                 "inventory, and freshness constraints."
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
#             and offer.quantity <= self.MAX_DEAL_QUANTITY
#             and offer.quantity <= self.state.available_capacity
#             and offer.quantity <= market_state.available_quantity
#             and offer.price_per_unit > 0
#             and offer.price_per_unit <= self.state.max_willingness_to_pay
#             # Initial offers may intentionally be below reservation price.
#             and offer.quantity * offer.price_per_unit <= self.state.budget
#             and offer.minimum_remaining_shelf_life_days
#             >= self.state.minimum_required_shelf_life_days
#             and market_state.remaining_shelf_life_days
#             >= offer.minimum_remaining_shelf_life_days
#         )

#     def _validate_ai_decision(
#         self,
#         decision: Decision,
#         incoming_offer: Offer,
#         market_state: MarketState,
#     ) -> Optional[Decision]:
#         if decision.action == ActionType.ACCEPT:
#             if (
#                 incoming_offer.buyer_id != self.state.retailer_id
#                 or incoming_offer.seller_id != "distributor"
#                 or incoming_offer.quantity > self.MAX_DEAL_QUANTITY
#                 or incoming_offer.price_per_unit <= 0
#                 or incoming_offer.quantity <= 0
#                 or incoming_offer.price_per_unit
#                 > self.state.max_willingness_to_pay
#                 or incoming_offer.price_per_unit
#                 < market_state.distributor_reservation_price
#                 or incoming_offer.quantity > self.state.available_capacity
#                 or incoming_offer.quantity > market_state.available_quantity
#                 or incoming_offer.quantity * incoming_offer.price_per_unit
#                 > self.state.budget
#                 or market_state.remaining_shelf_life_days
#                 < self.state.minimum_required_shelf_life_days
#                 or incoming_offer.minimum_remaining_shelf_life_days
#                 < self.state.minimum_required_shelf_life_days
#                 or market_state.remaining_shelf_life_days
#                 < incoming_offer.minimum_remaining_shelf_life_days
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
#             if decision.offer.quantity > self.MAX_DEAL_QUANTITY:
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

"""Budget retailer agent.

The budget retailer is price-sensitive and may purchase larger quantities.
AI decisions are optional; hard budget, capacity, inventory, and freshness
constraints are validated in Python.
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


class BudgetRetailerAgent(BaseAgent):
    MAX_DEAL_QUANTITY = 100
    def __init__(
        self,
        state: RetailerState,
        ai_enabled: Optional[bool] = None,
    ):
        super().__init__(state.retailer_id)
        self.state = state

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

    def make_initial_offer(self, market_state: MarketState) -> Optional[Offer]:
        """Create a valid opening offer, falling back safely if resources are exhausted."""
        rule_offer = self._make_rule_based_initial_offer(market_state)

        # Do not construct an AI fallback around an impossible opening offer.
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
            retailer_role="budget grocery retailer",
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
        """Respond safely, using AI for eligible counteroffer decisions."""

        rule_decision = self._rule_based_response(offer, market_state)

        # Preserve deterministic decisions for acceptance and hard constraints.
        if rule_decision.action in {
            ActionType.ACCEPT,
            ActionType.WALK_AWAY,
        }:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_decision

        # If AI is disabled, use the deterministic counteroffer.
        if not self.ai_enabled:
            self.last_decision_source = "RULE"
            self.ai_metrics["rule_based_decisions"] += 1
            return rule_decision

        prompt = retailer_response_prompt(
            retailer_role="budget grocery retailer",
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

        # Reject invalid AI output and safely fall back to the rule decision.
        if validated is None:
            if self.ai_provider.last_source == "ai":
                self.ai_metrics["invalid_ai_responses"] += 1
            self.last_decision_source = "FALLBACK"
            self.ai_metrics["fallbacks"] += 1
            return rule_decision

        # Report whether the provider actually supplied the decision.
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
        """Build a feasible opening bid, or return None to walk away safely."""
        reservation = market_state.distributor_reservation_price
        max_price = self.state.max_willingness_to_pay

        # The opening bid may be below reservation, but it must be feasible
        # for the retailer's actual resources.
        if (
            reservation <= 0
            or max_price <= 0
            or self.state.budget <= 0
            or self.state.available_capacity <= 0
            or market_state.available_quantity <= 0
            or market_state.remaining_shelf_life_days
            < self.state.minimum_required_shelf_life_days
        ):
            return None

        price = round(min(max_price, reservation * 0.80), 2)
        if price <= 0:
            return None

        affordable_quantity = int(self.state.budget // price)
        desired_quantity = max(1, int(self.state.sales_velocity_per_day * 2))
        
        # Opening offers express the retailer's two-day demand target.
        # The deal limit is enforced when a deal is validated/executed.
        quantity = min(
            self.state.available_capacity,
            market_state.available_quantity,
            affordable_quantity,
            desired_quantity,
        )

        if quantity <= 0:
            return None

        return Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=round(max(0.01, price), 2),
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
        """Accept valid offers; otherwise make a safe, affordable counteroffer."""
        max_price = self.state.max_willingness_to_pay
        required_shelf_life = self.state.minimum_required_shelf_life_days
        reservation_price = market_state.distributor_reservation_price

        # Reject invalid offers or situations where a purchase is impossible.
        if (
            offer.price_per_unit <= 0
            or offer.quantity <= 0
            or market_state.available_quantity <= 0
            or self.state.available_capacity <= 0
            or self.state.budget <= 0
            or market_state.remaining_shelf_life_days < required_shelf_life
            or offer.minimum_remaining_shelf_life_days < required_shelf_life
            or market_state.remaining_shelf_life_days
            < offer.minimum_remaining_shelf_life_days
        ):
            return Decision(
                action=ActionType.WALK_AWAY,
                reason=(
                    "Offer is invalid or fails budget, capacity, inventory, "
                    "or freshness requirements."
                ),
            )

        # Accept only when all business constraints are satisfied.
        total_cost = offer.price_per_unit * offer.quantity
        if (
            offer.price_per_unit >= reservation_price
            and offer.quantity <= self.MAX_DEAL_QUANTITY
            and offer.price_per_unit <= max_price
            and offer.quantity <= self.state.available_capacity
            and offer.quantity <= market_state.available_quantity
            and total_cost <= self.state.budget
        ):
            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Budget retailer accepts: price, budget, capacity, "
                    "inventory, and freshness checks passed."
                ),
            )

        # Walk away when there is no overlap between the buyer's maximum
        # price and the distributor's minimum acceptable price.
        if reservation_price <= 0 or max_price < reservation_price:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason="No mutually acceptable positive price exists.",
            )

        # Aim for a compromise between the incoming price and the
        # retailer's maximum willingness to pay, while respecting the
        # distributor's reservation price.
        target_price = (offer.price_per_unit + max_price) / 2

        counter_price = round(
            max(
                reservation_price,
                min(max_price, target_price),
            ),
            2,
        )

        if (
            counter_price <= 0
            or counter_price < reservation_price
            or counter_price > max_price
        ):
            return Decision(
                action=ActionType.WALK_AWAY,
                reason="No valid counteroffer price is available.",
            )

        # Calculate the maximum quantity the retailer can afford.
        affordable_quantity = int(self.state.budget // counter_price)
        counter_quantity = min(
            offer.quantity,
            self.MAX_DEAL_QUANTITY,
            max(0, self.state.available_capacity),
            max(0, market_state.available_quantity),
            max(0, affordable_quantity),
        )

        if counter_quantity <= 0:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason=(
                    "Budget retailer cannot afford any units "
                    "at a mutually acceptable price."
                ),
            )

        counter_offer = Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=counter_price,
            quantity=counter_quantity,
            minimum_remaining_shelf_life_days=required_shelf_life,
        )

        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Budget retailer proposes a compromise price and an "
                "affordable quantity while respecting budget, capacity, "
                "inventory, and freshness constraints."
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
            and offer.quantity <= self.MAX_DEAL_QUANTITY
            and offer.quantity <= self.state.available_capacity
            and offer.quantity <= market_state.available_quantity
            and offer.price_per_unit > 0
            and offer.price_per_unit <= self.state.max_willingness_to_pay
            # Initial offers may intentionally be below reservation price.
            and offer.quantity * offer.price_per_unit <= self.state.budget
            and offer.minimum_remaining_shelf_life_days
            >= self.state.minimum_required_shelf_life_days
            and market_state.remaining_shelf_life_days
            >= offer.minimum_remaining_shelf_life_days
        )

    def _validate_ai_decision(
        self,
        decision: Decision,
        incoming_offer: Offer,
        market_state: MarketState,
    ) -> Optional[Decision]:
        if decision.action == ActionType.ACCEPT:
            if (
                incoming_offer.buyer_id != self.state.retailer_id
                or incoming_offer.seller_id != "distributor"
                or incoming_offer.quantity > self.MAX_DEAL_QUANTITY
                or incoming_offer.price_per_unit <= 0
                or incoming_offer.quantity <= 0
                or incoming_offer.price_per_unit
                > self.state.max_willingness_to_pay
                or incoming_offer.price_per_unit
                < market_state.distributor_reservation_price
                or incoming_offer.quantity > self.state.available_capacity
                or incoming_offer.quantity > market_state.available_quantity
                or incoming_offer.quantity * incoming_offer.price_per_unit
                > self.state.budget
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
            if decision.offer.quantity > self.MAX_DEAL_QUANTITY:
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
