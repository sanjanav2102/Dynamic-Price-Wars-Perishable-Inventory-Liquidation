from models.schemas import (
    MarketState,
    AgentType,
    RetailerState,
    ActionType,
)

from agents.distributor import (
    DistributorAgent,
)

from agents.premium_retailer import (
    PremiumRetailerAgent,
)


def create_market():

    return MarketState(

        round_number=1,

        total_inventory=500,

        remaining_inventory=500,

        total_shelf_life_days=5,

        remaining_shelf_life_days=5,

        distributor_reservation_price=100,
    )


def test_distributor_accepts_good_offer():

    distributor = DistributorAgent()

    market = create_market()

    retailer = RetailerState(

        retailer_id="premium_grocery",

        retailer_type=(
            AgentType.PREMIUM_RETAILER
        ),

        storage_capacity=100,

        current_inventory=0,

        sales_velocity_per_day=30,

        max_willingness_to_pay=110,

        minimum_required_shelf_life_days=2,

        budget=10000,
    )

    offer = retailer

    from models.schemas import Offer

    offer = Offer(

        buyer_id="premium_grocery",

        seller_id="distributor",

        price_per_unit=105,

        quantity=20,

        minimum_remaining_shelf_life_days=2,
    )

    decision = distributor.respond_to_offer(
        offer,
        market,
    )

    assert decision.action == ActionType.ACCEPT


def test_premium_retailer_creates_offer():

    market = create_market()

    state = RetailerState(

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

    agent = PremiumRetailerAgent(state)

    offer = agent.make_initial_offer(market)

    assert offer.quantity > 0

    assert offer.price_per_unit > 0