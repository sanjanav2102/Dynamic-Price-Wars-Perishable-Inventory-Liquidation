from models.schemas import (
    Offer,
    AgentType,
    RetailerState,
)

from environment.validation import (
    DealValidator,
)


def create_retailer():

    return RetailerState(

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


def test_valid_offer():

    validator = DealValidator()

    retailer = create_retailer()

    offer = Offer(

        buyer_id="premium_grocery",

        seller_id="distributor",

        price_per_unit=100,

        quantity=50,

        minimum_remaining_shelf_life_days=2,
    )

    valid, reason = validator.validate_offer(

        offer=offer,

        distributor_stock=500,

        distributor_reservation_price=95,

        current_remaining_shelf_life_days=5,

        retailer=retailer,
    )

    assert valid is True


def test_reject_quantity_above_inventory():

    validator = DealValidator()

    retailer = create_retailer()

    offer = Offer(

        buyer_id="premium_grocery",

        seller_id="distributor",

        price_per_unit=100,

        quantity=600,

        minimum_remaining_shelf_life_days=2,
    )

    valid, reason = validator.validate_offer(

        offer=offer,

        distributor_stock=500,

        distributor_reservation_price=95,

        current_remaining_shelf_life_days=5,

        retailer=retailer,
    )

    assert valid is False


def test_reject_price_below_reservation():

    validator = DealValidator()

    retailer = create_retailer()

    offer = Offer(

        buyer_id="premium_grocery",

        seller_id="distributor",

        price_per_unit=80,

        quantity=50,

        minimum_remaining_shelf_life_days=2,
    )

    valid, reason = validator.validate_offer(

        offer=offer,

        distributor_stock=500,

        distributor_reservation_price=95,

        current_remaining_shelf_life_days=5,

        retailer=retailer,
    )

    assert valid is False