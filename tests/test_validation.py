
from models.schemas import AgentType, MarketState, RetailerState, Offer
from environment.validation import DealValidator


def make_market():
    return MarketState(
        day=3,
        product_name="Fresh Milk",
        available_quantity=100,
        remaining_shelf_life_days=8,
        distributor_reservation_price=84.0,
    )


def make_retailer():
    return RetailerState(
        retailer_id=AgentType.RETAILER_A,
        capacity=60,
        current_inventory=0,
        sales_velocity=10.0,
        max_willingness_to_pay=90.0,
        minimum_shelf_life_days=2,
        budget=5000.0,
    )


def make_offer(**overrides):
    data = {
        "seller_id": AgentType.DISTRIBUTOR,
        "buyer_id": AgentType.RETAILER_A,
        "quantity": 10,
        "unit_price": 85.0,
        "minimum_remaining_shelf_life_days": 2,
    }
    data.update(overrides)
    return Offer(**data)


def test_valid_offer_is_accepted():
    valid, message = DealValidator.validate_offer(
        make_offer(), make_market(), make_retailer()
    )
    assert valid is True


def test_offer_below_reservation_price_is_rejected():
    valid, message = DealValidator.validate_offer(
        make_offer(unit_price=80.0), make_market(), make_retailer()
    )
    assert valid is False
    assert "reservation" in message.lower()


def test_offer_exceeding_stock_is_rejected():
    valid, message = DealValidator.validate_offer(
        make_offer(quantity=101), make_market(), make_retailer()
    )
    assert valid is False
    assert "inventory" in message.lower()


def test_offer_exceeding_retailer_capacity_is_rejected():
    valid, message = DealValidator.validate_offer(
        make_offer(quantity=61), make_market(), make_retailer()
    )
    assert valid is False
    assert "capacity" in message.lower()
