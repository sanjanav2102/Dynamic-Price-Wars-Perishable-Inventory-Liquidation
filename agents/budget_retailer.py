'''This retailer:

is more price-sensitive
has greater storage capacity
has lower willingness to pay
may purchase larger quantities'''

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
        super().__init__(state)

        self.state = state

    def make_initial_offer(
        self,
        market_state: MarketState,
    ) -> Offer:

        reservation = (
            market_state.distributor_reservation_price
        )

        price = min(
            self.state.max_willingness_to_pay,
            reservation * 0.80,
        )

        quantity = min(
            self.state.available_capacity,
            int(
                self.state.sales_velocity_per_day
                * 3
            ),
        )

        quantity = max(
            1,
            quantity,
        )

        return Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",

            price_per_unit=round(
                price,
                2
            ),

            quantity=quantity,

            minimum_remaining_shelf_life_days=(
                self.state.minimum_required_shelf_life_days
            ),
        )

    def respond_to_counter(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        max_price = (
            self.state.max_willingness_to_pay
        )

        if offer.price_per_unit <= max_price:

            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Counteroffer is within "
                    "budget retailer willingness to pay."
                ),
            )

        # Budget retailer counters lower.

        counter_price = (
            max_price
            + offer.price_per_unit
        ) / 2

        counter_price = min(
            counter_price,
            max_price,
        )

        counter_offer = Offer(
            buyer_id=self.state.retailer_id,
            seller_id="distributor",

            price_per_unit=round(
                counter_price,
                2
            ),

            quantity=offer.quantity,

            minimum_remaining_shelf_life_days=(
                self.state.minimum_required_shelf_life_days
            ),
        )

        return Decision(
            action=ActionType.COUNTER,
            offer=counter_offer,
            reason=(
                "Counteroffer exceeds budget retailer "
                "willingness to pay."
            ),
        )