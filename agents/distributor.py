'''The distributor wants:

high price
sell inventory before expiry
avoid selling below reservation price'''



from agents.base_agent import BaseAgent

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
    ):
        super().__init__(agent_id)

    def respond_to_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:

        reservation_price = (
            market_state.distributor_reservation_price
        )

        # -----------------------------------------
        # Accept if price is good enough
        # -----------------------------------------

        if offer.price_per_unit >= reservation_price:

            return Decision(
                action=ActionType.ACCEPT,
                offer=offer,
                reason=(
                    "Offer meets or exceeds "
                    "distributor reservation price."
                ),
            )

        # -----------------------------------------
        # Counteroffer
        # -----------------------------------------

        # As expiry approaches,
        # distributor becomes more flexible.

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
                reservation_price
            ),
            2
        )

        counter_offer = Offer(
            buyer_id=offer.buyer_id,
            seller_id=offer.seller_id,

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
                "Offer is below reservation price; "
                "distributor is countering."
            ),
        )