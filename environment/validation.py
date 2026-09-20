
from models.schemas import Offer, MarketState, RetailerState, AgentType


class DealValidator:
    @staticmethod
    def validate_offer(
        offer: Offer,
        market: MarketState,
        retailer: RetailerState,
    ) -> tuple[bool, str]:
        """Check whether an offer follows all market rules."""

        # Only the distributor can sell
        if offer.seller_id != AgentType.DISTRIBUTOR:
            return False, "Seller must be the distributor."

        # Only retailers can buy
        if offer.buyer_id != retailer.retailer_id:
            return False, "Offer buyer does not match retailer."

        # Check available stock
        if offer.quantity > market.available_quantity:
            return False, "Not enough distributor inventory."

        # Check retailer storage capacity
        if offer.quantity > retailer.available_capacity:
            return False, "Retailer does not have enough capacity."

        # Check minimum acceptable distributor price
        if offer.unit_price < market.distributor_reservation_price:
            return False, "Offer price is below distributor reservation price."

        # Check retailer's maximum willingness to pay
        if offer.unit_price > retailer.max_willingness_to_pay:
            return False, "Offer price exceeds retailer's maximum price."

        # Check retailer budget
        total_cost = offer.quantity * offer.unit_price
        if total_cost > retailer.budget:
            return False, "Retailer does not have enough budget."

        # Check product freshness
        if (
            market.remaining_shelf_life_days
            < retailer.minimum_shelf_life_days
        ):
            return False, "Product does not meet retailer's freshness requirement."

        if (
            market.remaining_shelf_life_days
            < offer.minimum_remaining_shelf_life_days
        ):
            return False, "Product does not meet offer's freshness requirement."

        return True, "Offer is valid."
