import pytest

from environment.inventory import (
    InventoryManager,
)


def test_inventory_can_be_sold():

    inventory = InventoryManager(500)

    assert inventory.can_sell(100)


def test_selling_reduces_inventory():

    inventory = InventoryManager(500)

    inventory.sell(100)

    assert inventory.remaining_inventory == 400


def test_cannot_sell_more_than_available():

    inventory = InventoryManager(100)

    with pytest.raises(ValueError):

        inventory.sell(101)


def test_expiry_moves_remaining_inventory():

    inventory = InventoryManager(500)

    inventory.sell(200)

    expired = (
        inventory.expire_all_remaining()
    )

    assert expired == 300

    assert inventory.remaining_inventory == 0

    assert inventory.expired_inventory == 300