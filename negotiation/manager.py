
# # from models.schemas import (
# #     MarketState,
# #     Offer,
# #     Decision,
# #     ActionType,
# #     NegotiationEvent,
# #     NegotiationResult,
# # )

# # from negotiation.protocol import (
# #     MAX_NEGOTIATION_TURNS,
# # )

# # from agents.distributor import DistributorAgent
# # from agents.premium_retailer import (
# #     PremiumRetailerAgent,
# # )
# # from agents.budget_retailer import (
# #     BudgetRetailerAgent,
# # )

# # from environment.market import (
# #     MarketEnvironment,
# # )


# # class NegotiationManager:

# #     def __init__(
# #         self,
# #         environment: MarketEnvironment,
# #         distributor: DistributorAgent,
# #         retailers: dict,
# #     ):

# #         self.environment = environment
# #         self.distributor = distributor
# #         self.retailers = retailers

# #     # =========================================================
# #     # Main negotiation
# #     # =========================================================

    
# #     def negotiate(self, retailer_id: str) -> NegotiationResult:
# #         """Run a bounded negotiation between a retailer and distributor."""

# #         if retailer_id not in self.retailers:
# #             raise KeyError(f"Unknown retailer: {retailer_id}")

# #         retailer = self.retailers[retailer_id]
# #         market_state = self.environment.get_market_state()
# #         events = []
# #         turns_used = 0

# #         current_offer = retailer.make_initial_offer(market_state)
# #         retailer_source = getattr(retailer, "last_decision_source", "RULE")

# #         def record_event(actor, decision, source, turn):
# #             offer = decision.offer
# #             events.append(
# #                 NegotiationEvent(
# #                     round_number=market_state.round_number,
# #                     turn_number=turn,
# #                     actor=actor,
# #                     action=decision.action,
# #                     price_per_unit=(
# #                         offer.price_per_unit if offer else None
# #                     ),
# #                     quantity=offer.quantity if offer else None,
# #                     minimum_remaining_shelf_life_days=(
# #                         offer.minimum_remaining_shelf_life_days
# #                         if offer else None
# #                     ),
# #                     reason=f"{decision.reason} [{source}]",
# #                 )
# #             )

# #         def finish(success, reason, final_offer, deal_result=None):
# #             return NegotiationResult(
# #                 success=success,
# #                 buyer_id=retailer_id,
# #                 seller_id="distributor",
# #                 final_offer=final_offer,
# #                 deal_result=deal_result,
# #                 turns_used=turns_used,
# #                 events=events,
# #                 reason=reason,
# #             )

# #         # Resource exhaustion is a normal outcome, not a simulation crash.
# #         if current_offer is None:
# #             self.environment.metrics.record_failed_negotiation()
# #             return finish(
# #                 False,
# #                 "Retailer walked away: no feasible initial offer within "
# #                 "remaining budget, capacity, inventory, and shelf-life constraints.",
# #                 None,
# #             )

# #         def execute_accepted_deal(offer):
# #             """Execute only offers that pass the environment's validation."""
# #             result = self.environment.execute_deal(offer)
# #             if result.success:
# #                 return finish(
# #                     True,
# #                     "Negotiation successful.",
# #                     offer,
# #                     result,
# #                 )

# #             return finish(
# #                 False,
# #                 f"Deal rejected by environment: {result.message}",
# #                 offer,
# #                 result,
# #             )

# #         while turns_used < MAX_NEGOTIATION_TURNS:
# #             turns_used += 1

# #             # After the opening bid, the retailer responds to the distributor's
# #             # latest offer. An ACCEPT must close the negotiation immediately.
# #             if turns_used == 1:
# #                 retailer_decision = Decision(
# #                     action=ActionType.COUNTER,
# #                     offer=current_offer,
# #                     reason=f"Initial retailer offer [{retailer_source}].",
# #                 )
# #             else:
# #                 retailer_decision = retailer.respond_to_counter(
# #                     current_offer,
# #                     market_state,
# #                 )
# #                 retailer_source = getattr(
# #                     retailer,
# #                     "last_decision_source",
# #                     "RULE",
# #                 )

# #             record_event(
# #                 retailer_id,
# #                 retailer_decision,
# #                 retailer_source,
# #                 turns_used,
# #             )

# #             if retailer_decision.action in {
# #                 ActionType.REJECT,
# #                 ActionType.WALK_AWAY,
# #             }:
# #                 self.environment.metrics.record_failed_negotiation()
# #                 return finish(
# #                     False,
# #                     "Retailer ended the negotiation.",
# #                     current_offer,
# #                 )

# #             if retailer_decision.action == ActionType.ACCEPT:
# #                 accepted_offer = retailer_decision.offer or current_offer
# #                 return execute_accepted_deal(accepted_offer)

# #             if retailer_decision.action != ActionType.COUNTER:
# #                 self.environment.metrics.record_failed_negotiation()
# #                 return finish(
# #                     False,
# #                     "Retailer returned an unsupported action.",
# #                     current_offer,
# #                 )

# #             if retailer_decision.offer is None:
# #                 self.environment.metrics.record_failed_negotiation()
# #                 return finish(
# #                     False,
# #                     "Retailer produced a counteroffer without an offer.",
# #                     current_offer,
# #                 )

# #             current_offer = retailer_decision.offer

# #             # Ask the distributor to evaluate the retailer's offer.
# #             distributor_decision = self.distributor.respond_to_offer(
# #                 current_offer,
# #                 market_state,
# #             )
# #             distributor_source = getattr(
# #                 self.distributor,
# #                 "last_decision_source",
# #                 "RULE",
# #             )

# #             # A seller counteroffer must also be feasible for this buyer.
# #             # AI may suggest a valid seller price but an unaffordable quantity.
# #             # Reduce quantity deterministically rather than bypassing the budget.
# #             if (
# #                 distributor_decision.action == ActionType.COUNTER
# #                 and distributor_decision.offer is not None
# #             ):
# #                 proposed = distributor_decision.offer
# #                 if proposed.price_per_unit > 0:
# #                     affordable_quantity = int(
# #                         retailer.state.budget // proposed.price_per_unit
# #                     )
# #                     feasible_quantity = min(
# #                         proposed.quantity,
# #                         market_state.available_quantity,
# #                         retailer.state.available_capacity,
# #                         affordable_quantity,
# #                         100,
# #                     )
# #                     if 0 < feasible_quantity < proposed.quantity:
# #                         adjusted_offer = proposed.model_copy(
# #                             update={"quantity": feasible_quantity}
# #                         )
# #                         distributor_decision = distributor_decision.model_copy(
# #                             update={
# #                                 "offer": adjusted_offer,
# #                                 "reason": (
# #                                     f"{distributor_decision.reason} "
# #                                     f"Quantity adjusted from {proposed.quantity} "
# #                                     f"to {feasible_quantity} to respect buyer "
# #                                     "budget, capacity, inventory, and deal limit."
# #                                 ),
# #                             }
# #                         )

# #             # Log the offer after feasibility checks so the log shows the
# #             # actual counteroffer passed to the retailer.
# #             record_event(
# #                 "distributor",
# #                 distributor_decision,
# #                 distributor_source,
# #                 turns_used,
# #             )

# #             if distributor_decision.action == ActionType.ACCEPT:
# #                 # The accepted offer is the retailer's offer.
# #                 return execute_accepted_deal(current_offer)

# #             if distributor_decision.action in {
# #                 ActionType.REJECT,
# #                 ActionType.WALK_AWAY,
# #             }:
# #                 self.environment.metrics.record_failed_negotiation()
# #                 return finish(
# #                     False,
# #                     "Distributor rejected the negotiation.",
# #                     current_offer,
# #                 )

# #             if (
# #                 distributor_decision.action != ActionType.COUNTER
# #                 or distributor_decision.offer is None
# #             ):
# #                 self.environment.metrics.record_failed_negotiation()
# #                 return finish(
# #                     False,
# #                     "Distributor returned an invalid counteroffer.",
# #                     current_offer,
# #                 )

# #             counter = distributor_decision.offer

# #             # Reject malformed or economically impossible counteroffers.
# #             if (
# #                 counter.seller_id != "distributor"
# #                 or counter.buyer_id != retailer_id
# #                 or counter.quantity <= 0
# #                 or counter.quantity > market_state.available_quantity
# #                 or counter.quantity > 100
# #                 or counter.price_per_unit
# #                 < market_state.distributor_reservation_price
# #                 or counter.price_per_unit <= 0
# #                 or counter.quantity > retailer.state.available_capacity
# #                 or counter.price_per_unit * counter.quantity
# #                 > retailer.state.budget
# #                 or market_state.remaining_shelf_life_days
# #                 < retailer.state.minimum_required_shelf_life_days
# #                 or counter.minimum_remaining_shelf_life_days
# #                 > market_state.remaining_shelf_life_days
# #             ):
# #                 self.environment.metrics.record_failed_negotiation()
# #                 return finish(
# #                     False,
# #                     "Distributor counteroffer failed business validation.",
# #                     current_offer,
# #                 )

# #             # The retailer gets the opportunity to accept, reject, or counter
# #             # this offer on the next loop iteration.
# #             current_offer = counter
# #             market_state = self.environment.get_market_state()

# #         self.environment.metrics.record_failed_negotiation()
# #         return finish(
# #             False,
# #             "Maximum negotiation turns reached.",
# #             current_offer,
# #         )

# from models.schemas import (
#     MarketState,
#     Offer,
#     Decision,
#     ActionType,
#     NegotiationEvent,
#     NegotiationResult,
# )

# from negotiation.protocol import (
#     MAX_NEGOTIATION_TURNS,
# )

# from agents.distributor import DistributorAgent
# from agents.premium_retailer import (
#     PremiumRetailerAgent,
# )
# from agents.budget_retailer import (
#     BudgetRetailerAgent,
# )

# from environment.market import (
#     MarketEnvironment,
# )


# class NegotiationManager:

#     def __init__(
#         self,
#         environment: MarketEnvironment,
#         distributor: DistributorAgent,
#         retailers: dict,
#     ):

#         self.environment = environment
#         self.distributor = distributor
#         self.retailers = retailers

#     # =========================================================
#     # Main negotiation
#     # =========================================================

    
#     def negotiate(self, retailer_id: str) -> NegotiationResult:
#         """Run a bounded negotiation between a retailer and distributor."""

#         if retailer_id not in self.retailers:
#             raise KeyError(f"Unknown retailer: {retailer_id}")

#         retailer = self.retailers[retailer_id]
#         market_state = self.environment.get_market_state()
#         events = []
#         turns_used = 0

#         current_offer = retailer.make_initial_offer(market_state)
#         retailer_source = getattr(retailer, "last_decision_source", "RULE")

#         def record_event(actor, decision, source, turn):
#             offer = decision.offer
#             events.append(
#                 NegotiationEvent(
#                     round_number=market_state.round_number,
#                     turn_number=turn,
#                     actor=actor,
#                     action=decision.action,
#                     price_per_unit=(
#                         offer.price_per_unit if offer else None
#                     ),
#                     quantity=offer.quantity if offer else None,
#                     minimum_remaining_shelf_life_days=(
#                         offer.minimum_remaining_shelf_life_days
#                         if offer else None
#                     ),
#                     reason=f"{decision.reason} [{source}]",
#                 )
#             )

#         def finish(success, reason, final_offer, deal_result=None):
#             return NegotiationResult(
#                 success=success,
#                 buyer_id=retailer_id,
#                 seller_id="distributor",
#                 final_offer=final_offer,
#                 deal_result=deal_result,
#                 turns_used=turns_used,
#                 events=events,
#                 reason=reason,
#             )

#         # Resource exhaustion is a normal outcome, not a simulation crash.
#         if current_offer is None:
#             self.environment.metrics.record_failed_negotiation()
#             return finish(
#                 False,
#                 "Retailer walked away: no feasible initial offer within "
#                 "remaining budget, capacity, inventory, and shelf-life constraints.",
#                 None,
#             )

#         def execute_accepted_deal(offer):
#             """Execute only offers that pass the environment's validation."""
#             result = self.environment.execute_deal(offer)
#             if result.success:
#                 return finish(
#                     True,
#                     "Negotiation successful.",
#                     offer,
#                     result,
#                 )

#             return finish(
#                 False,
#                 f"Deal rejected by environment: {result.message}",
#                 offer,
#                 result,
#             )

#         while turns_used < MAX_NEGOTIATION_TURNS:
#             turns_used += 1

#             # After the opening bid, the retailer responds to the distributor's
#             # latest offer. An ACCEPT must close the negotiation immediately.
#             if turns_used == 1:
#                 retailer_decision = Decision(
#                     action=ActionType.COUNTER,
#                     offer=current_offer,
#                     reason=f"Initial retailer offer [{retailer_source}].",
#                 )
#             else:
#                 retailer_decision = retailer.respond_to_counter(
#                     current_offer,
#                     market_state,
#                 )
#                 retailer_source = getattr(
#                     retailer,
#                     "last_decision_source",
#                     "RULE",
#                 )

#             record_event(
#                 retailer_id,
#                 retailer_decision,
#                 retailer_source,
#                 turns_used,
#             )

#             if retailer_decision.action in {
#                 ActionType.REJECT,
#                 ActionType.WALK_AWAY,
#             }:
#                 self.environment.metrics.record_failed_negotiation()
#                 return finish(
#                     False,
#                     "Retailer ended the negotiation.",
#                     current_offer,
#                 )

#             if retailer_decision.action == ActionType.ACCEPT:
#                 accepted_offer = retailer_decision.offer or current_offer
#                 return execute_accepted_deal(accepted_offer)

#             if retailer_decision.action != ActionType.COUNTER:
#                 self.environment.metrics.record_failed_negotiation()
#                 return finish(
#                     False,
#                     "Retailer returned an unsupported action.",
#                     current_offer,
#                 )

#             if retailer_decision.offer is None:
#                 self.environment.metrics.record_failed_negotiation()
#                 return finish(
#                     False,
#                     "Retailer produced a counteroffer without an offer.",
#                     current_offer,
#                 )

#             current_offer = retailer_decision.offer

#             # Ask the distributor to evaluate the retailer's offer.
#             distributor_decision = self.distributor.respond_to_offer(
#                 current_offer,
#                 market_state,
#             )
#             distributor_source = getattr(
#                 self.distributor,
#                 "last_decision_source",
#                 "RULE",
#             )

#             # A seller counteroffer must also be feasible for this buyer.
#             # AI may suggest a valid seller price but an unaffordable quantity.
#             # Reduce quantity deterministically rather than bypassing the budget.
#             if (
#                 distributor_decision.action == ActionType.COUNTER
#                 and distributor_decision.offer is not None
#             ):
#                 proposed = distributor_decision.offer
#                 if proposed.price_per_unit > 0:
#                     affordable_quantity = int(
#                         retailer.state.budget // proposed.price_per_unit
#                     )
#                     feasible_quantity = min(
#                         proposed.quantity,
#                         market_state.available_quantity,
#                         retailer.state.available_capacity,
#                         affordable_quantity,
#                         100,
#                     )
#                     if 0 < feasible_quantity < proposed.quantity:
#                         adjusted_offer = proposed.model_copy(
#                             update={"quantity": feasible_quantity}
#                         )
#                         distributor_decision = distributor_decision.model_copy(
#                             update={
#                                 "offer": adjusted_offer,
#                                 "reason": (
#                                     f"{distributor_decision.reason} "
#                                     f"Quantity adjusted from {proposed.quantity} "
#                                     f"to {feasible_quantity} to respect buyer "
#                                     "budget, capacity, inventory, and deal limit."
#                                 ),
#                             }
#                         )

#             # Log the offer after feasibility checks so the log shows the
#             # actual counteroffer passed to the retailer.
#             record_event(
#                 "distributor",
#                 distributor_decision,
#                 distributor_source,
#                 turns_used,
#             )

#             if distributor_decision.action == ActionType.ACCEPT:
#                 # The accepted offer is the retailer's offer.
#                 return execute_accepted_deal(current_offer)

#             if distributor_decision.action in {
#                 ActionType.REJECT,
#                 ActionType.WALK_AWAY,
#             }:
#                 self.environment.metrics.record_failed_negotiation()
#                 return finish(
#                     False,
#                     "Distributor rejected the negotiation.",
#                     current_offer,
#                 )

#             if (
#                 distributor_decision.action != ActionType.COUNTER
#                 or distributor_decision.offer is None
#             ):
#                 self.environment.metrics.record_failed_negotiation()
#                 return finish(
#                     False,
#                     "Distributor returned an invalid counteroffer.",
#                     current_offer,
#                 )

#             counter = distributor_decision.offer

#             # Reject malformed or economically impossible counteroffers.
#             if (
#                 counter.seller_id != "distributor"
#                 or counter.buyer_id != retailer_id
#                 or counter.quantity <= 0
#                 or counter.quantity > market_state.available_quantity
#                 or counter.quantity > 100
#                 or counter.price_per_unit
#                 < market_state.distributor_reservation_price
#                 or counter.price_per_unit <= 0
#                 or counter.quantity > retailer.state.available_capacity
#                 or counter.price_per_unit * counter.quantity
#                 > retailer.state.budget
#                 or market_state.remaining_shelf_life_days
#                 < retailer.state.minimum_required_shelf_life_days
#                 or counter.minimum_remaining_shelf_life_days
#                 > market_state.remaining_shelf_life_days
#             ):
#                 self.environment.metrics.record_failed_negotiation()
#                 return finish(
#                     False,
#                     "Distributor counteroffer failed business validation.",
#                     current_offer,
#                 )

#             # The retailer gets the opportunity to accept, reject, or counter
#             # this offer on the next loop iteration.
#             current_offer = counter
#             market_state = self.environment.get_market_state()

#         self.environment.metrics.record_failed_negotiation()
#         return finish(
#             False,
#             "Maximum negotiation turns reached.",
#             current_offer,
#         )

#     def get_ai_metrics(self) -> dict:
#         """Aggregate AI metrics across the distributor and retailer agents."""
#         totals = {
#             "ai_attempts": 0,
#             "ai_responses_received": 0,
#             "ai_decisions_used": 0,
#             "fallbacks": 0,
#         }
#         agents = [self.distributor, *self.retailers.values()]
#         for agent in agents:
#             getter = getattr(agent, "get_ai_metrics", None)
#             if getter:
#                 for key, value in getter().items():
#                     totals[key] = totals.get(key, 0) + value
#         return totals

from models.schemas import (
    MarketState,
    Offer,
    Decision,
    ActionType,
    NegotiationEvent,
    NegotiationResult,
)

from negotiation.protocol import (
    MAX_NEGOTIATION_TURNS,
)

from agents.distributor import DistributorAgent
from agents.premium_retailer import (
    PremiumRetailerAgent,
)
from agents.budget_retailer import (
    BudgetRetailerAgent,
)

from environment.market import (
    MarketEnvironment,
)


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

    # =========================================================
    # Main negotiation
    # =========================================================

    
    def negotiate(self, retailer_id: str) -> NegotiationResult:
        """Run a bounded negotiation between a retailer and distributor."""

        if retailer_id not in self.retailers:
            raise KeyError(f"Unknown retailer: {retailer_id}")

        retailer = self.retailers[retailer_id]
        market_state = self.environment.get_market_state()
        events = []
        turns_used = 0

        current_offer = retailer.make_initial_offer(market_state)
        retailer_source = getattr(retailer, "last_decision_source", "RULE")

        def record_event(actor, decision, source, turn):
            offer = decision.offer
            events.append(
                NegotiationEvent(
                    # The UI's market rounds advance with the market day. Some
                    # state snapshots keep round_number at its default value.
                    round_number=getattr(market_state, "day", market_state.round_number),
                    turn_number=turn,
                    actor=actor,
                    action=decision.action,
                    price_per_unit=(
                        offer.price_per_unit if offer else None
                    ),
                    quantity=offer.quantity if offer else None,
                    minimum_remaining_shelf_life_days=(
                        offer.minimum_remaining_shelf_life_days
                        if offer else None
                    ),
                    reason=f"{decision.reason.removesuffix(f' [{source}]')} [{source}]",
                )
            )

        def finish(success, reason, final_offer, deal_result=None):
            return NegotiationResult(
                success=success,
                buyer_id=retailer_id,
                seller_id="distributor",
                final_offer=final_offer,
                deal_result=deal_result,
                turns_used=turns_used,
                events=events,
                reason=reason,
            )

        # Resource exhaustion is a normal outcome, not a simulation crash.
        if current_offer is None:
            self.environment.metrics.record_failed_negotiation()
            return finish(
                False,
                "Retailer walked away: no feasible initial offer within "
                "remaining budget, capacity, inventory, and shelf-life constraints.",
                None,
            )

        def execute_accepted_deal(offer):
            """Execute only offers that pass the environment's validation."""
            result = self.environment.execute_deal(offer)
            if result.success:
                return finish(
                    True,
                    "Negotiation successful.",
                    offer,
                    result,
                )

            return finish(
                False,
                f"Deal rejected by environment: {result.message}",
                offer,
                result,
            )

        while turns_used < MAX_NEGOTIATION_TURNS:
            turns_used += 1

            # After the opening bid, the retailer responds to the distributor's
            # latest offer. An ACCEPT must close the negotiation immediately.
            if turns_used == 1:
                retailer_decision = Decision(
                    action=ActionType.COUNTER,
                    offer=current_offer,
                    reason=f"Initial retailer offer [{retailer_source}].",
                )
            else:
                retailer_decision = retailer.respond_to_counter(
                    current_offer,
                    market_state,
                )
                retailer_source = getattr(
                    retailer,
                    "last_decision_source",
                    "RULE",
                )

            record_event(
                retailer_id,
                retailer_decision,
                retailer_source,
                turns_used,
            )

            if retailer_decision.action in {
                ActionType.REJECT,
                ActionType.WALK_AWAY,
            }:
                self.environment.metrics.record_failed_negotiation()
                return finish(
                    False,
                    "Retailer ended the negotiation.",
                    current_offer,
                )

            if retailer_decision.action == ActionType.ACCEPT:
                accepted_offer = retailer_decision.offer or current_offer
                return execute_accepted_deal(accepted_offer)

            if retailer_decision.action != ActionType.COUNTER:
                self.environment.metrics.record_failed_negotiation()
                return finish(
                    False,
                    "Retailer returned an unsupported action.",
                    current_offer,
                )

            if retailer_decision.offer is None:
                self.environment.metrics.record_failed_negotiation()
                return finish(
                    False,
                    "Retailer produced a counteroffer without an offer.",
                    current_offer,
                )

            current_offer = retailer_decision.offer

            # Ask the distributor to evaluate the retailer's offer.
            distributor_decision = self.distributor.respond_to_offer(
                current_offer,
                market_state,
            )
            distributor_source = getattr(
                self.distributor,
                "last_decision_source",
                "RULE",
            )

            # A seller counteroffer must also be feasible for this buyer.
            # AI may suggest a valid seller price but an unaffordable quantity.
            # Reduce quantity deterministically rather than bypassing the budget.
            if (
                distributor_decision.action == ActionType.COUNTER
                and distributor_decision.offer is not None
            ):
                proposed = distributor_decision.offer
                if proposed.price_per_unit > 0:
                    affordable_quantity = int(
                        retailer.state.budget // proposed.price_per_unit
                    )
                    feasible_quantity = min(
                        proposed.quantity,
                        market_state.available_quantity,
                        retailer.state.available_capacity,
                        affordable_quantity,
                        100,
                    )
                    if 0 < feasible_quantity < proposed.quantity:
                        adjusted_offer = proposed.model_copy(
                            update={"quantity": feasible_quantity}
                        )
                        distributor_decision = distributor_decision.model_copy(
                            update={
                                "offer": adjusted_offer,
                                "reason": (
                                    f"{distributor_decision.reason} "
                                    f"Quantity adjusted from {proposed.quantity} "
                                    f"to {feasible_quantity} to respect buyer "
                                    "budget, capacity, inventory, and deal limit."
                                ),
                            }
                        )

            # Log the offer after feasibility checks so the log shows the
            # actual counteroffer passed to the retailer.
            record_event(
                "distributor",
                distributor_decision,
                distributor_source,
                turns_used,
            )

            if distributor_decision.action == ActionType.ACCEPT:
                # The accepted offer is the retailer's offer.
                return execute_accepted_deal(current_offer)

            if distributor_decision.action in {
                ActionType.REJECT,
                ActionType.WALK_AWAY,
            }:
                self.environment.metrics.record_failed_negotiation()
                return finish(
                    False,
                    "Distributor rejected the negotiation.",
                    current_offer,
                )

            if (
                distributor_decision.action != ActionType.COUNTER
                or distributor_decision.offer is None
            ):
                self.environment.metrics.record_failed_negotiation()
                return finish(
                    False,
                    "Distributor returned an invalid counteroffer.",
                    current_offer,
                )

            counter = distributor_decision.offer

            # Reject malformed or economically impossible counteroffers.
            if (
                counter.seller_id != "distributor"
                or counter.buyer_id != retailer_id
                or counter.quantity <= 0
                or counter.quantity > market_state.available_quantity
                or counter.quantity > 100
                or counter.price_per_unit
                < market_state.distributor_reservation_price
                or counter.price_per_unit <= 0
                or counter.quantity > retailer.state.available_capacity
                or counter.price_per_unit * counter.quantity
                > retailer.state.budget
                or market_state.remaining_shelf_life_days
                < retailer.state.minimum_required_shelf_life_days
                or counter.minimum_remaining_shelf_life_days
                > market_state.remaining_shelf_life_days
            ):
                self.environment.metrics.record_failed_negotiation()
                return finish(
                    False,
                    "Distributor counteroffer failed business validation.",
                    current_offer,
                )

            # The retailer gets the opportunity to accept, reject, or counter
            # this offer on the next loop iteration.
            current_offer = counter
            market_state = self.environment.get_market_state()

        self.environment.metrics.record_failed_negotiation()
        return finish(
            False,
            "Maximum negotiation turns reached.",
            current_offer,
        )

    def get_ai_metrics(self) -> dict:
        """Aggregate AI metrics across the distributor and retailer agents."""
        totals = {
            "ai_attempts": 0,
            "ai_responses_received": 0,
            "ai_decisions_used": 0,
            "invalid_ai_responses": 0,
            "fallbacks": 0,
            "rule_based_decisions": 0,
        }
        agents = [self.distributor, *self.retailers.values()]
        for agent in agents:
            getter = getattr(agent, "get_ai_metrics", None)
            if getter:
                for key, value in getter().items():
                    totals[key] = totals.get(key, 0) + value
        return totals
