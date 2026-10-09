

# """
# Premium retailer agent.

# This retailer:
# - Has higher willingness to pay
# - Has limited storage capacity
# - Sells inventory quickly
# - Prefers products with better remaining shelf life
# """

# from agents.base_agent import BaseAgent

# from models.schemas import (
#     MarketState,
#     RetailerState,
#     Offer,
#     Decision,
#     ActionType,
# )


# class PremiumRetailerAgent(BaseAgent):
#     def __init__(self, state: RetailerState):
#         super().__init__(state.retailer_id)
#         self.state = state

#     def make_initial_offer(
#         self,
#         market_state: MarketState,
#     ) -> Offer:
#         """Create the retailer's initial purchase offer."""

#         reservation = market_state.distributor_reservation_price

#         # Calculate available storage capacity.
#         available_capacity = max(
#             0,
#             self.state.available_capacity,
#         )

#         # Do not make a zero-quantity offer.
#         # Raise no exception; the simulation should skip
#         # retailers that have no available capacity.
#         if available_capacity == 0:
#             return Offer(
#                 buyer_id=self.state.retailer_id,
#                 seller_id="distributor",
#                 price_per_unit=0.0,
#                 quantity=0,
#                 minimum_remaining_shelf_life_days=(
#                     self.state.minimum_required_shelf_life_days
#                 ),
#             )

#         # Start slightly below the distributor's reservation
#         # price, without exceeding willingness to pay.
#         price = min(
#             self.state.max_willingness_to_pay,
#             reservation * 0.95,
#         )

#         # Limit quantity by storage capacity and expected sales.
#         quantity = min(
#             available_capacity,
#             max(
#                 1,
#                 int(self.state.sales_velocity_per_day * 2),
#             ),
#         )

#         return Offer(
#             buyer_id=self.state.retailer_id,
#             seller_id="distributor",
#             price_per_unit=round(price, 2),
#             quantity=quantity,
#             minimum_remaining_shelf_life_days=(
#                 self.state.minimum_required_shelf_life_days
#             ),
#         )

#     def respond_to_offer(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         """
#         Required BaseAgent method.
#         Delegate incoming offers to the retailer's counteroffer logic.
#         """
#         return self.respond_to_counter(
#             offer,
#             market_state,
#         )

#     def respond_to_counter(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:
#         """Accept an affordable offer or make a counteroffer."""

#         max_price = self.state.max_willingness_to_pay

#         available_capacity = max(
#             0,
#             self.state.available_capacity,
#         )

#         # Walk away if no storage capacity remains.
#         if available_capacity <= 0:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason=(
#                     "Premium retailer has no available capacity "
#                     "for the proposed quantity."
#                 ),
#             )

#         # Reject/counter offers that exceed the retailer's
#         # willingness to pay.
#         if offer.price_per_unit <= max_price:
#             # Ensure the proposed quantity fits available capacity.
#             if offer.quantity <= available_capacity:
#                 return Decision(
#                     action=ActionType.ACCEPT,
#                     offer=offer,
#                     reason=(
#                         "Premium retailer accepts because the price "
#                         "is within its willingness to pay and "
#                         "the quantity fits available capacity."
#                     ),
#                 )

#         # Calculate a midpoint counteroffer.
#         counter_price = (
#             offer.price_per_unit + max_price
#         ) / 2

#         # Never exceed the retailer's maximum willingness to pay.
#         counter_price = min(
#             counter_price,
#             max_price,
#         )

#         # Do not counter with more than available storage.
#         counter_quantity = min(
#             offer.quantity,
#             available_capacity,
#         )

#         if counter_quantity <= 0:
#             return Decision(
#                 action=ActionType.WALK_AWAY,
#                 reason=(
#                     "Premium retailer has no available capacity "
#                     "for the proposed quantity."
#                 ),
#             )

#         counter_offer = Offer(
#             buyer_id=self.state.retailer_id,
#             seller_id="distributor",
#             price_per_unit=round(counter_price, 2),
#             quantity=counter_quantity,
#             minimum_remaining_shelf_life_days=(
#                 self.state.minimum_required_shelf_life_days
#             ),
#         )

#         return Decision(
#             action=ActionType.COUNTER,
#             offer=counter_offer,
#             reason=(
#                 "Premium retailer is countering to stay within "
#                 "its price limit and available capacity."
#             ),
#         )
"""
Premium retailer agent.

Premium retailer:
- Has higher willingness to pay.
- Has limited storage capacity.
- Sells inventory quickly.
- Prefers products with better shelf life.
- Can optionally use an LLM for decisions.
"""

import os
from typing import Optional

from agents.base_agent import BaseAgent

from ai_strategy.provider import (
    LLMDecisionProvider,
)

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
        super().__init__(
            state.retailer_id
        )

        self.state = state

        if ai_enabled is None:
            value = os.getenv(
                "AI_ENABLED",
                "false",
            )

            ai_enabled = (
                value.lower()
                in {
                    "1",
                    "true",
                    "yes",
                    "on",
                }
            )

        self.ai_enabled = ai_enabled

        self.ai_provider = (
            LLMDecisionProvider(
                 enabled=ai_enabled,
                    timeout=45.0,
                    max_ai_calls=5,
            )
        )

        self.last_decision_source = "RULE"

    # =========================================================
    # Initial offer
    # =========================================================

    def make_initial_offer(
        self,
        market_state: MarketState,
    ) -> Offer:

        rule_offer = (
            self._make_rule_based_initial_offer(
                market_state
            )
        )

        if not self.ai_enabled:
            self.last_decision_source = "RULE"
            return rule_offer

        fallback_decision = Decision(
            action=ActionType.COUNTER,
            offer=rule_offer,
            reason=(
                "Rule-based fallback initial offer."
            ),
        )

        prompt = (
            retailer_initial_offer_prompt(
                retailer_role=(
                    "premium grocery retailer"
                ),
                market_state=market_state,
                retailer_state=self.state,
            )
        )

        decision = (
            self.ai_provider.get_decision(
                prompt,
                fallback=lambda: fallback_decision,
            )
        )

        if (
            decision.offer is None
            or not self._is_valid_ai_offer(
                decision.offer,
                market_state,
            )
        ):
            self.last_decision_source = "RULE"
            return rule_offer

        self.last_decision_source = (
            "AI"
            if self.ai_provider.last_source
            == "ai"
            else "FALLBACK"
        )

        return decision.offer

    # =========================================================
    # BaseAgent method
    # =========================================================

    def respond_to_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        return self.respond_to_counter(
            offer,
            market_state,
        )

    # =========================================================
    # Incoming distributor offer
    # =========================================================

    def respond_to_counter(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        rule_decision = (
            self._rule_based_response(
                offer,
                market_state,
            )
        )

        if not self.ai_enabled:
            self.last_decision_source = "RULE"
            return rule_decision

        prompt = (
            retailer_response_prompt(
                retailer_role=(
                    "premium grocery retailer"
                ),
                market_state=market_state,
                retailer_state=self.state,
                incoming_offer=offer,
            )
        )

        decision = (
            self.ai_provider.get_decision(
                prompt,
                fallback=lambda: rule_decision,
            )
        )

        validated = (
            self._validate_ai_decision(
                decision,
                offer,
                market_state,
            )
        )

        if validated is None:
            self.last_decision_source = "RULE"
            return rule_decision

        self.last_decision_source = (
            "AI"
            if self.ai_provider.last_source
            == "ai"
            else "FALLBACK"
        )

        return validated

    # =========================================================
    # Deterministic strategy
    # =========================================================

    def _make_rule_based_initial_offer(
        self,
        market_state: MarketState,
    ) -> Offer:

        reservation = (
            market_state
            .distributor_reservation_price
        )

        price = min(
            self.state.max_willingness_to_pay,
            reservation * 0.95,
        )

        quantity = min(
            self.state.available_capacity,
            max(
                1,
                int(
                    self.state
                    .sales_velocity_per_day
                    * 2
                ),
            ),
        )

        return Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=round(
                price,
                2,
            ),
            quantity=quantity,
            minimum_remaining_shelf_life_days=(
                self.state
                .minimum_required_shelf_life_days
            ),
        )

    def _rule_based_response(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        max_price = (
            self.state
            .max_willingness_to_pay
        )

        if offer.price_per_unit <= max_price:
            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Premium retailer accepts "
                    "because the price is within "
                    "willingness to pay."
                ),
            )

        counter_price = (
            offer.price_per_unit
            + max_price
        ) / 2

        counter_price = min(
            counter_price,
            max_price,
        )

        quantity = min(
            offer.quantity,
            self.state.available_capacity,
        )

        if quantity <= 0:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason=(
                    "Premium retailer has no "
                    "available storage capacity."
                ),
            )

        counter_offer = Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=round(
                counter_price,
                2,
            ),
            quantity=quantity,
            minimum_remaining_shelf_life_days=(
                self.state
                .minimum_required_shelf_life_days
            ),
        )

        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Premium retailer is countering "
                "to stay within its price limit."
            ),
        )

    # =========================================================
    # AI safety validation
    # =========================================================

    def _is_valid_ai_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> bool:

        if (
            offer.buyer_id
            != self.state.retailer_id
        ):
            return False

        if offer.seller_id != "distributor":
            return False

        if offer.quantity <= 0:
            return False

        if (
            offer.quantity
            > self.state.available_capacity
        ):
            return False

        if (
            offer.price_per_unit
            > self.state.max_willingness_to_pay
        ):
            return False

        if (
            offer.quantity
            * offer.price_per_unit
            > self.state.budget
        ):
            return False

        if (
            offer.minimum_remaining_shelf_life_days
            < self.state.minimum_required_shelf_life_days
        ):
            return False

        if (
            market_state.remaining_shelf_life_days
            < offer.minimum_remaining_shelf_life_days
        ):
            return False

        return True

    def _validate_ai_decision(
        self,
        decision: Decision,
        incoming_offer: Offer,
        market_state: MarketState,
    ) -> Optional[Decision]:

        if decision.action == ActionType.ACCEPT:
            if (
                incoming_offer.price_per_unit > self.state.max_willingness_to_pay
                or incoming_offer.quantity > self.state.available_capacity
                or incoming_offer.quantity > market_state.available_quantity
                or incoming_offer.quantity * incoming_offer.price_per_unit > self.state.budget
                or market_state.remaining_shelf_life_days
                < self.state.minimum_required_shelf_life_days
                or incoming_offer.price_per_unit
                < market_state.distributor_reservation_price
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
                reason=(
                    decision.reason
                    or "AI walked away."
                ),
            )

        if decision.action == ActionType.COUNTER:

            if decision.offer is None:
                return None

            if not self._is_valid_ai_offer(
                decision.offer,
                market_state,
            ):
                return None

            return Decision(
                action=ActionType.COUNTER,
                offer=decision.offer,
                reason=(
                    decision.reason
                    or "AI generated a counteroffer."
                ),
            )

        return None