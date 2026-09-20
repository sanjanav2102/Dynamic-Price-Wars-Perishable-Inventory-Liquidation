
from environment.market import MarketEnvironment
from models.schemas import Offer, AgentType


def make_offer(
    quantity=10,
    unit_price=85.0,
    buyer=AgentType.RETAILER_A,
):
    return Offer(
        seller_id=AgentType.DISTRIBUTOR,
        buyer_id=buyer,
        quantity=quantity,
        unit_price=unit_price,
        minimum_remaining_shelf_life_days=2,
    )


def test_successful_deal_updates_market():
    market = MarketEnvironment()
    market.advance_day()
    market.advance_day()

    result = market.execute_deal(make_offer())

    assert result.accepted is True
    assert market.inventory.available_quantity == 90
    assert market.get_retailer_state(
        AgentType.RETAILER_A
    ).budget == 4150.0
    assert market.metrics.total_revenue == 850.0


def test_rejected_deal_does_not_change_inventory_or_budget():
    market = MarketEnvironment()

    original_inventory = market.inventory.available_quantity
    original_budget = market.get_retailer_state(
        AgentType.RETAILER_A
    ).budget

    # Day 1 reservation price is 100; offer is too low
    result = market.execute_deal(make_offer(unit_price=80.0))

    assert result.accepted is False
    assert market.inventory.available_quantity == original_inventory
    assert market.get_retailer_state(
        AgentType.RETAILER_A
    ).budget == original_budget


def test_advance_day_reduces_shelf_life():
    market = MarketEnvironment()

    market.advance_day()

    assert market.day == 2
    assert market.remaining_shelf_life_days == 9


def test_stock_expires_when_shelf_life_reaches_zero():
    market = MarketEnvironment()

    # Advance through the 10-day shelf life
    for _ in range(10):
        market.advance_day()

    assert market.remaining_shelf_life_days == 0
    assert market.inventory.available_quantity == 0
    assert market.inventory.expired_quantity == 100
