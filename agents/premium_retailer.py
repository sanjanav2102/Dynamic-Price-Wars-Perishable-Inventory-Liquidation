
"""
Premium retailer agent.

This retailer:
- Has higher willingness to pay
- Has limited storage capacity
- Sells inventory quickly
- Prefers products with better remaining shelf life
"""

from agents.base_agent import BaseAgent

from models.schemas import (
    MarketState,
    RetailerState,
    Offer,
    Decision,
    ActionType,
)


class PremiumRetailerAgent(BaseAgent):
    def __init__(self, state: RetailerState):
        super().__init__(state.retailer_id)
        self.state = state

    def make_initial_offer(
        self,
        market_state: MarketState,
    ) -> Offer:
        """Create the retailer's initial purchase offer."""

        reservation = market_state.distributor_reservation_price

        # Calculate available storage capacity.
        available_capacity = max(
            0,
            self.state.available_capacity,
        )

        # Do not make a zero-quantity offer.
        # Raise no exception; the simulation should skip
        # retailers that have no available capacity.
        if available_capacity == 0:
            return Offer(
                buyer_id=self.state.retailer_id,
                seller_id="distributor",
                price_per_unit=0.0,
                quantity=0,
                minimum_remaining_shelf_life_days=(
                    self.state.minimum_required_shelf_life_days
                ),
            )

        # Start slightly below the distributor's reservation
        # price, without exceeding willingness to pay.
        price = min(
            self.state.max_willingness_to_pay,
            reservation * 0.95,
        )

        # Limit quantity by storage capacity and expected sales.
        quantity = min(
            available_capacity,
            max(
                1,
                int(self.state.sales_velocity_per_day * 2),
            ),
        )

        return Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=round(price, 2),
            quantity=quantity,
            minimum_remaining_shelf_life_days=(
                self.state.minimum_required_shelf_life_days
            ),
        )

    def respond_to_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        """
        Required BaseAgent method.
        Delegate incoming offers to the retailer's counteroffer logic.
        """
        return self.respond_to_counter(
            offer,
            market_state,
        )

    def respond_to_counter(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        """Accept an affordable offer or make a counteroffer."""

        max_price = self.state.max_willingness_to_pay

        available_capacity = max(
            0,
            self.state.available_capacity,
        )

        # Walk away if no storage capacity remains.
        if available_capacity <= 0:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason=(
                    "Premium retailer has no available capacity "
                    "for the proposed quantity."
                ),
            )

        # Reject/counter offers that exceed the retailer's
        # willingness to pay.
        if offer.price_per_unit <= max_price:
            # Ensure the proposed quantity fits available capacity.
            if offer.quantity <= available_capacity:
                return Decision(
                    action=ActionType.ACCEPT,
                    offer=offer,
                    reason=(
                        "Premium retailer accepts because the price "
                        "is within its willingness to pay and "
                        "the quantity fits available capacity."
                    ),
                )

        # Calculate a midpoint counteroffer.
        counter_price = (
            offer.price_per_unit + max_price
        ) / 2

        # Never exceed the retailer's maximum willingness to pay.
        counter_price = min(
            counter_price,
            max_price,
        )

        # Do not counter with more than available storage.
        counter_quantity = min(
            offer.quantity,
            available_capacity,
        )

        if counter_quantity <= 0:
            return Decision(
                action=ActionType.WALK_AWAY,
                reason=(
                    "Premium retailer has no available capacity "
                    "for the proposed quantity."
                ),
            )

        counter_offer = Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=round(counter_price, 2),
            quantity=counter_quantity,
            minimum_remaining_shelf_life_days=(
                self.state.minimum_required_shelf_life_days
            ),
        )

        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Premium retailer is countering to stay within "
                "its price limit and available capacity."
            ),
        )
