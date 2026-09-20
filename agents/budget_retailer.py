
"""
Budget retailer agent.

This retailer:
- Is more price-sensitive
- Has greater storage capacity
- Has lower willingness to pay
- May purchase larger quantities
"""

from agents.base_agent import BaseAgent

from models.schemas import (
    MarketState,
    RetailerState,
    Offer,
    Decision,
    ActionType,
)


class BudgetRetailerAgent(BaseAgent):

    def __init__(
        self,
        state: RetailerState,
    ):
        super().__init__(state.retailer_id)
        self.state = state

    def make_initial_offer(
        self,
        market_state: MarketState,
    ) -> Offer:
        """Create the budget retailer's initial offer."""

        reservation = (
            market_state.distributor_reservation_price
        )

        price = min(
            self.state.max_willingness_to_pay,
            reservation * 0.80,
        )

        quantity = min(
            self.state.available_capacity,
            max(
                1,
                int(
                    self.state.sales_velocity_per_day * 3
                ),
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
        Respond to an offer using the budget retailer's
        existing counter-offer strategy.
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
        """Accept an affordable offer or make a counter-offer."""

        max_price = self.state.max_willingness_to_pay

        # Accept if the price is within the retailer's limit.
        if offer.price_per_unit <= max_price:
            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Budget retailer accepts because "
                    "the price is within its maximum "
                    "willingness to pay."
                ),
            )

        # Otherwise, counter with a price no higher
        # than the retailer's maximum willingness to pay.
        counter_price = (
            offer.price_per_unit + max_price
        ) / 2

        counter_price = min(
            counter_price,
            max_price,
        )

        counter_offer = Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",
            price_per_unit=round(counter_price, 2),
            quantity=offer.quantity,
            minimum_remaining_shelf_life_days=(
                self.state.minimum_required_shelf_life_days
            ),
        )

        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Budget retailer is countering "
                "because the price is too high."
            ),
        )
