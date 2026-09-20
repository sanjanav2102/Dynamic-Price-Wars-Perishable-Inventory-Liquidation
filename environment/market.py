
from models.schemas import (
    AgentType,
    MarketState,
    RetailerState,
    Offer,
    DealResult,
)

from environment.pricing import calculate_reservation_price
from environment.inventory import InventoryManager
from environment.validation import DealValidator
from environment.metrics import SimulationMetrics


class MarketEnvironment:
    def __init__(
        self,
        product_name="Fresh Milk",
        initial_quantity=100,
        total_shelf_life_days=10,
        initial_price=100.0,
        minimum_price=20.0,
        *,
        initial_inventory=None,
        initial_reservation_price=None,
        minimum_reservation_price=None,
        retailers=None,
    ):
        # Support both original and integration constructor arguments
        if initial_inventory is not None:
            initial_quantity = initial_inventory

        if initial_reservation_price is not None:
            initial_price = initial_reservation_price

        if minimum_reservation_price is not None:
            minimum_price = minimum_reservation_price

        # Product and pricing information
        self.product_name = product_name
        self.day = 1
        self.round_number = 1

        self.total_shelf_life_days = total_shelf_life_days
        self.remaining_shelf_life_days = total_shelf_life_days

        self.initial_price = initial_price
        self.minimum_price = minimum_price

        # Inventory manager
        self.inventory = InventoryManager(initial_quantity)

        # Performance tracker
        self.metrics = SimulationMetrics()

        # Retailer states
        if retailers is not None:
            self.retailers = retailers
        else:
            self.retailers = {
                AgentType.RETAILER_A: RetailerState(
                    retailer_id=AgentType.RETAILER_A,
                    capacity=60,
                    current_inventory=0,
                    sales_velocity=10.0,
                    max_willingness_to_pay=90.0,
                    minimum_shelf_life_days=2,
                    budget=5000.0,
                ),
                AgentType.RETAILER_B: RetailerState(
                    retailer_id=AgentType.RETAILER_B,
                    capacity=50,
                    current_inventory=0,
                    sales_velocity=8.0,
                    max_willingness_to_pay=85.0,
                    minimum_shelf_life_days=3,
                    budget=4000.0,
                ),
            }

    def get_reservation_price(self) -> float:
        """Get the distributor's current minimum acceptable price."""
        return calculate_reservation_price(
            initial_price=self.initial_price,
            minimum_price=self.minimum_price,
            remaining_shelf_life_days=self.remaining_shelf_life_days,
            total_shelf_life_days=self.total_shelf_life_days,
        )

    def get_market_state(self) -> MarketState:
        """Return the current market information."""
        return MarketState(
            day=self.day,
            product_name=self.product_name,
            available_quantity=self.inventory.available_quantity,
            remaining_shelf_life_days=self.remaining_shelf_life_days,
            distributor_reservation_price=self.get_reservation_price(),
        )

    def get_retailer_state(self, retailer_id) -> RetailerState:
        """Return the current state of a retailer."""
        if retailer_id not in self.retailers:
            raise ValueError("Unknown retailer.")

        return self.retailers[retailer_id]

    def execute_deal(self, offer: Offer) -> DealResult:
        """Validate and execute a proposed deal."""

        retailer = self.retailers.get(offer.buyer_id)

        # Support string retailer IDs when keys use enums
        if retailer is None:
            for key, state in self.retailers.items():
                if str(getattr(key, "value", key)) == str(offer.buyer_id):
                    retailer = state
                    break

        if retailer is None:
            self.metrics.record_rejected_offer()
            return DealResult(
                accepted=False,
                quantity=offer.quantity,
                unit_price=offer.unit_price,
                total_cost=0.0,
                message="Unknown retailer.",
            )

        # Validate before changing inventory or retailer funds
        market_state = self.get_market_state()

        is_valid, message = DealValidator.validate_offer(
            offer,
            market_state,
            retailer,
        )

        if not is_valid:
            self.metrics.record_rejected_offer()
            return DealResult(
                accepted=False,
                quantity=offer.quantity,
                unit_price=offer.unit_price,
                total_cost=0.0,
                message=message,
            )

        # Execute the valid deal
        total_cost = offer.quantity * offer.unit_price

        self.inventory.sell(offer.quantity)
        retailer.current_inventory += offer.quantity
        retailer.budget -= total_cost

        self.metrics.record_successful_deal(
            offer.quantity,
            offer.unit_price,
        )

        return DealResult(
            accepted=True,
            quantity=offer.quantity,
            unit_price=offer.unit_price,
            total_cost=round(total_cost, 2),
            message="Deal completed successfully.",
        )

    def record_failed_negotiation(self) -> None:
        """Record a negotiation that ended without a deal."""
        self.metrics.record_failed_negotiation()

    def advance_day(self) -> None:
        """Move the simulation forward by one day."""

        if self.remaining_shelf_life_days <= 0:
            return

        self.day += 1
        self.round_number += 1
        self.remaining_shelf_life_days -= 1

        # Expire distributor stock when shelf life reaches zero
        if self.remaining_shelf_life_days == 0:
            self.inventory.expire_remaining_stock()

    def get_status(self) -> dict:
        """Return a summary of the current simulation."""

        inventory_state = self.inventory.get_state()
        metrics_summary = self.metrics.get_summary()

        # Add compatibility alias expected by end-to-end tests.
        # Use the existing summary value rather than assuming
        # a particular internal SimulationMetrics attribute.
        total_units_sold = metrics_summary.get(
            "total_units_sold",
            metrics_summary.get("units_sold", 0),
        )

        metrics_summary["total_units_sold"] = total_units_sold

        return {
            "day": self.day,
            "product_name": self.product_name,
            "remaining_shelf_life_days": self.remaining_shelf_life_days,
            "distributor_reservation_price": self.get_reservation_price(),

            # Inventory summary keys
            "remaining_inventory": self.inventory.available_quantity,
            "expired_inventory": self.inventory.expired_quantity,

            # Detailed inventory state
            "inventory": inventory_state,

            # Retailer states
            "retailers": {
                str(getattr(retailer_id, "value", retailer_id)): (
                    retailer.model_dump()
                )
                for retailer_id, retailer in self.retailers.items()
            },

            # Simulation metrics
            "metrics": metrics_summary,
        }
