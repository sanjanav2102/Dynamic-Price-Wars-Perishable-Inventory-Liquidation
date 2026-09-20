
import pytest

from environment.pricing import calculate_reservation_price


def test_fresh_product_has_initial_price():
    price = calculate_reservation_price(100, 20, 10, 10)
    assert price == 100.0


def test_expiring_product_has_minimum_price():
    price = calculate_reservation_price(100, 20, 0, 10)
    assert price == 20.0


def test_price_decreases_as_shelf_life_decreases():
    fresh_price = calculate_reservation_price(100, 20, 10, 10)
    older_price = calculate_reservation_price(100, 20, 5, 10)

    assert older_price < fresh_price


def test_negative_shelf_life_raises_error():
    with pytest.raises(ValueError):
        calculate_reservation_price(100, 20, -1, 10)
