'''This retailer:

has higher willingness to pay
has limited capacity
sells quickly
prefers better shelf life'''

from agents.base_agent import BaseAgent

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
    ):
        super().__init__(state.retailer_id)

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
            reservation * 0.95,
        )

        quantity = min(
            self.state.available_capacity,
            max(
                1,
                int(
                    self.state.sales_velocity_per_day
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

    def respond_to_counter(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        max_price = (
            self.state.max_willingness_to_pay
        )

        # Accept if price is affordable.

        if offer.price_per_unit <= max_price:

            return Decision(
                action=ActionType.ACCEPT,

                offer=offer,

                reason=(
                    "Premium retailer accepts because "
                    "price is within willingness to pay."
                ),
            )

        # If price is too high,
        # create midpoint counteroffer.

        counter_price = (
            offer.price_per_unit
            + max_price
        ) / 2

        # If the midpoint is still above the
        # maximum affordable price, cap it.

        counter_price = min(
            counter_price,
            max_price,
        )

        counter_offer = Offer(

            buyer_id=self.state.retailer_id,

            seller_id="distributor",

            price_per_unit=round(
                counter_price,
                2,
            ),

            quantity=offer.quantity,

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