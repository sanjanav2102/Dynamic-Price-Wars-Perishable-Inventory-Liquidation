from environment.market import (
    MarketEnvironment,
)

from agents.distributor import (
    DistributorAgent,
)

from agents.premium_retailer import (
    PremiumRetailerAgent,
)

from models.schemas import (
    AgentType,
    RetailerState,
)

from negotiation.manager import (
    NegotiationManager,
)


def test_negotiation_has_turn_limit():

    retailer_state = RetailerState(

        retailer_id="premium_grocery",

        retailer_type=(
            AgentType.PREMIUM_RETAILER
        ),

        storage_capacity=100,

        current_inventory=0,

        sales_velocity_per_day=30,

        max_willingness_to_pay=105,

        minimum_required_shelf_life_days=2,

        budget=10000,
    )

    environment = MarketEnvironment(

        initial_inventory=500,

        total_shelf_life_days=5,

        initial_reservation_price=100,

        minimum_reservation_price=60,

        retailers={
            "premium_grocery": retailer_state
        },
    )

    distributor = DistributorAgent()

    retailer = PremiumRetailerAgent(
        retailer_state
    )

    manager = NegotiationManager(

        environment=environment,

        distributor=distributor,

        retailers={
            "premium_grocery": retailer
        },
    )

    result = manager.negotiate(
        "premium_grocery"
    )

    assert result.turns_used <= 6