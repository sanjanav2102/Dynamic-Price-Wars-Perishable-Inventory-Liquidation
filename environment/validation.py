
from typing import Optional

from models.schemas import Offer, MarketState, RetailerState


class DealValidator:

    @staticmethod
    def validate_offer(
        offer: Offer,
        market: Optional[MarketState] = None,
        retailer: Optional[RetailerState] = None,
        *,
        distributor_stock: Optional[int] = None,
        distributor_reservation_price: Optional[float] = None,
        current_remaining_shelf_life_days: Optional[int] = None,
    ) -> tuple[bool, str]:

        # Use MarketState values when provided.
        if market is not None:
            distributor_stock = market.available_quantity
            distributor_reservation_price = (
                market.distributor_reservation_price
            )
            current_remaining_shelf_life_days = (
                market.remaining_shelf_life_days
            )

        if retailer is None:
            return False, "Retailer state is required."

        if distributor_stock is None:
            return False, "Distributor stock is required."

        if distributor_reservation_price is None:
            return False, "Distributor reservation price is required."

        if current_remaining_shelf_life_days is None:
            return False, "Remaining shelf life is required."

        # Check seller and buyer.
        if offer.seller_id != "distributor":
            return False, "Seller must be the distributor."

        if offer.buyer_id != retailer.retailer_id:
            return False, "Offer buyer does not match retailer."

        # Check inventory.
        if offer.quantity > distributor_stock:
            return False, "Not enough distributor inventory."

        # Check retailer capacity.
        if offer.quantity > retailer.available_capacity:
            return False, "Retailer does not have enough capacity."

        # Check price limits.
        if offer.price_per_unit < distributor_reservation_price:
            return False, (
                "Offer price is below distributor reservation price."
            )

        if offer.price_per_unit > retailer.max_willingness_to_pay:
            return False, (
                "Offer price exceeds retailer's maximum price."
            )

        # Check retailer budget.
        total_cost = offer.quantity * offer.price_per_unit

        if total_cost > retailer.budget:
            return False, "Retailer does not have enough budget."

        # Check freshness.
        if (
            current_remaining_shelf_life_days
            < retailer.minimum_shelf_life_days
        ):
            return False, (
                "Product does not meet retailer's freshness requirement."
            )

        if (
            current_remaining_shelf_life_days
            < offer.minimum_remaining_shelf_life_days
        ):
            return False, (
                "Product does not meet offer's freshness requirement."
            )

        return True, "Offer is valid."
