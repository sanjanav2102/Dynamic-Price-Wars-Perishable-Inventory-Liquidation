# '''The distributor wants:

# high price
# sell inventory before expiry
# avoid selling below reservation price'''



# from agents.base_agent import BaseAgent

# from models.schemas import (
#     MarketState,
#     Offer,
#     Decision,
#     ActionType,
# )


# class DistributorAgent(BaseAgent):

#     def __init__(
#         self,
#         agent_id: str = "distributor",
#     ):
#         super().__init__(agent_id)

#     def respond_to_offer(
#         self,
#         offer: Offer,
#         market_state: MarketState,
#     ) -> Decision:

#         reservation_price = (
#             market_state.distributor_reservation_price
#         )

#         # -----------------------------------------
#         # Accept if price is good enough
#         # -----------------------------------------

#         if offer.price_per_unit >= reservation_price:

#             return Decision(
#                 action=ActionType.ACCEPT,
#                 offer=offer,
#                 reason=(
#                     "Offer meets or exceeds "
#                     "distributor reservation price."
#                 ),
#             )

#         # -----------------------------------------
#         # Counteroffer
#         # -----------------------------------------

#         # As expiry approaches,
#         # distributor becomes more flexible.

#         price_gap = (
#             reservation_price
#             - offer.price_per_unit
#         )

#         counter_price = (
#             offer.price_per_unit
#             + price_gap * 0.6
#         )

#         counter_price = round(
#             max(
#                 counter_price,
#                 reservation_price
#             ),
#             2
#         )

#         counter_offer = Offer(
#             buyer_id=offer.buyer_id,
#             seller_id=offer.seller_id,

#             price_per_unit=counter_price,

#             quantity=offer.quantity,

#             minimum_remaining_shelf_life_days=(
#                 offer.minimum_remaining_shelf_life_days
#             ),
#         )

#         return Decision(
#             action=ActionType.COUNTER,
#             offer=counter_offer,
#             reason=(
#                 "Offer is below reservation price; "
#                 "distributor is countering."
#             ),
#         )

"""
Distributor agent.

The distributor:
- Wants a reasonable selling price.
- Wants to sell inventory before expiry.
- Must not sell below reservation price.
- Can optionally use an LLM.
"""

import os
from typing import Optional

from agents.base_agent import BaseAgent

from ai_strategy.provider import (
    LLMDecisionProvider,
)

from ai_strategy.prompts import (
    distributor_response_prompt,
)

from models.schemas import (
    MarketState,
    Offer,
    Decision,
    ActionType,
)


class DistributorAgent(BaseAgent):

    def __init__(
        self,
        agent_id: str = "distributor",
        ai_enabled: Optional[bool] = None,
    ):
        super().__init__(agent_id)

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
    # Incoming retailer offer
    # =========================================================

    def respond_to_offer(
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
            distributor_response_prompt(
                market_state=market_state,
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
    # Rule-based distributor strategy
    # =========================================================

    def _rule_based_response(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        reservation_price = (
            market_state
            .distributor_reservation_price
        )

        if (
            offer.price_per_unit
            >= reservation_price
        ):
            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Offer meets or exceeds "
                    "distributor reservation price."
                ),
            )

        price_gap = (
            reservation_price
            - offer.price_per_unit
        )

        counter_price = (
            offer.price_per_unit
            + price_gap * 0.6
        )

        counter_price = round(
            max(
                counter_price,
                reservation_price,
            ),
            2,
        )

        counter_offer = Offer(
            buyer_id=offer.buyer_id,
            seller_id="distributor",
            price_per_unit=counter_price,
            quantity=offer.quantity,
            minimum_remaining_shelf_life_days=(
                offer.minimum_remaining_shelf_life_days
            ),
        )

        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Offer is below reservation "
                "price; distributor is "
                "countering."
            ),
        )

    # =========================================================
    # AI validation
    # =========================================================

    def _validate_ai_decision(
        self,
        decision: Decision,
        incoming_offer: Offer,
        market_state: MarketState,
    ) -> Optional[Decision]:

        reservation = (
            market_state
            .distributor_reservation_price
        )

        if decision.action == ActionType.ACCEPT:

            # IMPORTANT:
            # When accepting, use the actual incoming
            # offer rather than trusting the LLM to
            # modify the transaction.
            if (
                incoming_offer.price_per_unit
                < reservation
            ):
                return None

            if (
                incoming_offer.quantity
                > market_state.available_quantity
            ):
                return None

            return Decision(
                action=ActionType.ACCEPT,
                offer=incoming_offer,
                reason=(
                    decision.reason
                    or "AI accepted the offer."
                ),
            )

        if decision.action == ActionType.REJECT:

            return Decision(
                action=ActionType.REJECT,
                reason=(
                    decision.reason
                    or "AI rejected the offer."
                ),
            )

        if decision.action == ActionType.COUNTER:

            if decision.offer is None:
                return None

            counter = decision.offer

            if counter.seller_id != "distributor":
                return None

            if (
                counter.buyer_id
                != incoming_offer.buyer_id
            ):
                return None

            if counter.quantity <= 0:
                return None

            if (
                counter.quantity
                > market_state.available_quantity
            ):
                return None

            if (
                counter.price_per_unit
                < reservation
            ):
                return None

            return Decision(
                action=ActionType.COUNTER,
                offer=counter,
                reason=(
                    decision.reason
                    or "AI generated a counteroffer."
                ),
            )

        return None