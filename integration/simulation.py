
from environment.market import MarketEnvironment

from agents.distributor import DistributorAgent
from agents.premium_retailer import PremiumRetailerAgent
from agents.budget_retailer import BudgetRetailerAgent

from negotiation.manager import NegotiationManager

from models.schemas import (
    AgentType,
    RetailerState,
)


class PriceWarSimulation:

    def __init__(self):

        # =========================================
        # 1. Create retailer states
        # =========================================

        premium_state = RetailerState(
            retailer_id="premium_grocery",
            retailer_type=AgentType.PREMIUM_RETAILER,
            storage_capacity=150,
            current_inventory=0,
            sales_velocity_per_day=50,
            max_willingness_to_pay=105.0,
            minimum_required_shelf_life_days=2,
            budget=15000.0,
        )

        budget_state = RetailerState(
            retailer_id="budget_mart",
            retailer_type=AgentType.BUDGET_RETAILER,
            storage_capacity=250,
            current_inventory=0,
            sales_velocity_per_day=70,
            max_willingness_to_pay=90.0,
            minimum_required_shelf_life_days=1,
            budget=18000.0,
        )

        retailers = {
            "premium_grocery": premium_state,
            "budget_mart": budget_state,
        }

        # =========================================
        # 2. Create environment
        # =========================================

        self.environment = MarketEnvironment(
            initial_inventory=500,
            total_shelf_life_days=5,
            initial_reservation_price=100.0,
            minimum_reservation_price=60.0,
            retailers=retailers,
        )

        # =========================================
        # 3. Create distributor agent
        # =========================================

        self.distributor = DistributorAgent()

        # =========================================
        # 4. Create retailer agents
        # =========================================

        self.premium_retailer = PremiumRetailerAgent(
            premium_state
        )

        self.budget_retailer = BudgetRetailerAgent(
            budget_state
        )

        # =========================================
        # 5. Create negotiation manager
        # =========================================

        self.negotiation_manager = NegotiationManager(
            environment=self.environment,
            distributor=self.distributor,
            retailers={
                "premium_grocery": self.premium_retailer,
                "budget_mart": self.budget_retailer,
            },
        )

        self.results = []

    def run_round(self) -> None:

        print()
        print("=" * 60)
        print(
            f"MARKET ROUND "
            f"{self.environment.round_number}"
        )
        print("=" * 60)

        state = self.environment.get_market_state()

        print(
            f"Remaining inventory: "
            f"{state.remaining_inventory}"
        )

        print(
            f"Remaining shelf life: "
            f"{state.remaining_shelf_life_days} days"
        )

        print(
            f"Distributor reservation price: "
            f"₹{state.distributor_reservation_price:.2f}"
        )

        # =========================================
        # Premium retailer negotiates
        # =========================================

        if (
            state.remaining_inventory > 0
            and self.premium_retailer.state.available_capacity > 0
        ):
            result = self.negotiation_manager.negotiate(
                "premium_grocery"
            )

            self.results.append(result)
            self._print_result(result)

        else:
            print(
                "\nSkipping premium_grocery: "
                "no inventory or storage capacity."
            )

        # =========================================
        # Budget retailer negotiates
        # =========================================

        state = self.environment.get_market_state()

        if (
            state.remaining_inventory > 0
            and self.budget_retailer.state.available_capacity > 0
        ):
            result = self.negotiation_manager.negotiate(
                "budget_mart"
            )

            self.results.append(result)
            self._print_result(result)

        else:
            print(
                "\nSkipping budget_mart: "
                "no inventory or storage capacity."
            )

        # =========================================
        # Advance time
        # =========================================

        if self.environment.remaining_shelf_life_days > 0:
            self.environment.advance_day()

    def _print_result(self, result) -> None:

        print()

        print(
            f"Negotiation: "
            f"{result.buyer_id} vs "
            f"{result.seller_id}"
        )

        print(f"Success: {result.success}")
        print(f"Turns used: {result.turns_used}")
        print(f"Reason: {result.reason}")

        if result.deal_result:
            deal = result.deal_result

            print(f"Deal quantity: {deal.quantity}")

            print(
                f"Deal price: "
                f"₹{deal.price_per_unit:.2f}"
            )

            print(
                f"Deal value: "
                f"₹{deal.total_value:.2f}"
            )

    def run(self) -> None:

        print()
        print("#" * 60)
        print("DYNAMIC PRICE WARS SIMULATION")
        print("#" * 60)

        # Run until product expires or inventory becomes zero.

        while (
            self.environment.remaining_shelf_life_days > 0
            and self.environment.inventory.remaining_inventory > 0
        ):
            self.run_round()

        # =========================================
        # Final status
        # =========================================

        print()
        print("#" * 60)
        print("FINAL RESULTS")
        print("#" * 60)

        status = self.environment.get_status()

        # Print the status dictionary without assuming
        # particular keys exist.

        for key, value in status.items():

            if isinstance(value, dict):
                print(f"\n{key.replace('_', ' ').title()}:")

                for nested_key, nested_value in value.items():
                    print(
                        f"  {nested_key.replace('_', ' ').title()}: "
                        f"{nested_value}"
                    )

            else:
                print(
                    f"{key.replace('_', ' ').title()}: "
                    f"{value}"
                )

        print()
