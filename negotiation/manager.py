
from models.schemas import (
    MarketState,
    Offer,
    Decision,
    ActionType,
    NegotiationEvent,
    NegotiationResult,
)

from negotiation.protocol import MAX_NEGOTIATION_TURNS

from agents.distributor import DistributorAgent
from agents.premium_retailer import PremiumRetailerAgent
from agents.budget_retailer import BudgetRetailerAgent

from environment.market import MarketEnvironment


class NegotiationManager:
    def __init__(
        self,
        environment: MarketEnvironment,
        distributor: DistributorAgent,
        retailers: dict,
    ):
        self.environment = environment
        self.distributor = distributor
        self.retailers = retailers

    def negotiate(
        self,
        retailer_id: str,
    ) -> NegotiationResult:

        if retailer_id not in self.retailers:
            raise KeyError(
                f"Unknown retailer: {retailer_id}"
            )

        retailer = self.retailers[retailer_id]

        market_state = self.environment.get_market_state()

        # -----------------------------------------
        # Check retailer storage capacity
        # -----------------------------------------

        if retailer.state.available_capacity <= 0:
            self.environment.metrics.record_failed_negotiation()

            return NegotiationResult(
                success=False,
                buyer_id=retailer_id,
                seller_id="distributor",
                final_offer=None,
                deal_result=None,
                turns_used=0,
                events=[],
                reason=(
                    "Retailer has no available storage capacity."
                ),
            )

        # -----------------------------------------
        # Initial offer
        # -----------------------------------------

        current_offer = retailer.make_initial_offer(
            market_state
        )

        events = []
        turns_used = 0

        # -----------------------------------------
        # Negotiation loop
        # -----------------------------------------

        while turns_used < MAX_NEGOTIATION_TURNS:
            turns_used += 1

            # =====================================
            # Retailer offer / counter
            # =====================================

            if turns_used == 1:
                retailer_decision = Decision(
                    action=ActionType.COUNTER,
                    offer=current_offer,
                    reason="Initial retailer offer.",
                )
            else:
                retailer_decision = retailer.respond_to_counter(
                    current_offer,
                    market_state,
                )

            events.append(
                NegotiationEvent(
                    round_number=market_state.round_number,
                    turn_number=turns_used,
                    actor=retailer_id,
                    action=retailer_decision.action,
                    price_per_unit=(
                        retailer_decision.offer.price_per_unit
                        if retailer_decision.offer
                        else None
                    ),
                    quantity=(
                        retailer_decision.offer.quantity
                        if retailer_decision.offer
                        else None
                    ),
                    minimum_remaining_shelf_life_days=(
                        retailer_decision.offer.minimum_remaining_shelf_life_days
                        if retailer_decision.offer
                        else None
                    ),
                    reason=retailer_decision.reason,
                )
            )

            if retailer_decision.offer is None:
                break

            current_offer = retailer_decision.offer

            # =====================================
            # Distributor responds
            # =====================================

            distributor_decision = self.distributor.respond_to_offer(
                current_offer,
                market_state,
            )

            events.append(
                NegotiationEvent(
                    round_number=market_state.round_number,
                    turn_number=turns_used,
                    actor="distributor",
                    action=distributor_decision.action,
                    price_per_unit=(
                        distributor_decision.offer.price_per_unit
                        if distributor_decision.offer
                        else None
                    ),
                    quantity=(
                        distributor_decision.offer.quantity
                        if distributor_decision.offer
                        else None
                    ),
                    minimum_remaining_shelf_life_days=(
                        distributor_decision.offer.minimum_remaining_shelf_life_days
                        if distributor_decision.offer
                        else None
                    ),
                    reason=distributor_decision.reason,
                )
            )

            # =====================================
            # Distributor accepts
            # =====================================

            if distributor_decision.action == ActionType.ACCEPT:
                deal_result = self.environment.execute_deal(
                    current_offer
                )

                if deal_result.success:
                    return NegotiationResult(
                        success=True,
                        buyer_id=retailer_id,
                        seller_id="distributor",
                        final_offer=current_offer,
                        deal_result=deal_result,
                        turns_used=turns_used,
                        events=events,
                        reason="Negotiation successful.",
                    )

                # Environment rejected the deal.
                return NegotiationResult(
                    success=False,
                    buyer_id=retailer_id,
                    seller_id="distributor",
                    final_offer=current_offer,
                    deal_result=deal_result,
                    turns_used=turns_used,
                    events=events,
                    reason=(
                        "Agent accepted, but "
                        "environment rejected the deal."
                    ),
                )

            # =====================================
            # Distributor rejects
            # =====================================

            if distributor_decision.action == ActionType.REJECT:
                self.environment.metrics.record_failed_negotiation()

                return NegotiationResult(
                    success=False,
                    buyer_id=retailer_id,
                    seller_id="distributor",
                    final_offer=current_offer,
                    deal_result=None,
                    turns_used=turns_used,
                    events=events,
                    reason="Distributor rejected the negotiation.",
                )

            # =====================================
            # Distributor counters
            # =====================================

            if distributor_decision.action == ActionType.COUNTER:
                if distributor_decision.offer is None:
                    self.environment.metrics.record_failed_negotiation()

                    return NegotiationResult(
                        success=False,
                        buyer_id=retailer_id,
                        seller_id="distributor",
                        final_offer=current_offer,
                        deal_result=None,
                        turns_used=turns_used,
                        events=events,
                        reason=(
                            "Distributor produced an invalid "
                            "counteroffer."
                        ),
                    )

                current_offer = distributor_decision.offer

                market_state = self.environment.get_market_state()

        # -----------------------------------------
        # Maximum turns reached / negotiation ended
        # -----------------------------------------

        self.environment.metrics.record_failed_negotiation()

        return NegotiationResult(
            success=False,
            buyer_id=retailer_id,
            seller_id="distributor",
            final_offer=current_offer,
            deal_result=None,
            turns_used=turns_used,
            events=events,
            reason=(
                "Maximum negotiation turns reached."
                if turns_used >= MAX_NEGOTIATION_TURNS
                else "Retailer ended the negotiation."
            ),
        )
