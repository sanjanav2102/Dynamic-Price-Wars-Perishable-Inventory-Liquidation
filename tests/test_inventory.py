
import pytest

from environment.inventory import InventoryManager


def test_sell_updates_inventory():
    inventory = InventoryManager(100)

    inventory.sell(20)

    state = inventory.get_state()
    assert state["available_quantity"] == 80
    assert state["sold_quantity"] == 20


def test_cannot_sell_more_than_available():
    inventory = InventoryManager(100)

    with pytest.raises(ValueError):
        inventory.sell(150)


def test_expire_remaining_stock():
    inventory = InventoryManager(100)
    inventory.sell(20)

    expired = inventory.expire_remaining_stock()

    assert expired == 80
    assert inventory.get_state()["available_quantity"] == 0
    assert inventory.get_state()["expired_quantity"] == 80


def test_cannot_expire_more_than_available():
    inventory = InventoryManager(100)

    with pytest.raises(ValueError):
        inventory.expire_quantity(150)
