from environment.pricing import calculate_reservation_price


def test_full_shelf_life_has_initial_price():
    price = calculate_reservation_price(
        initial_price=100,
        minimum_price=60,
        total_shelf_life_days=5,
        remaining_shelf_life_days=5,
    )

    assert price == 100


def test_expiry_reaches_minimum_price():
    price = calculate_reservation_price(
        initial_price=100,
        minimum_price=60,
        total_shelf_life_days=5,
        remaining_shelf_life_days=0,
    )

    assert price == 60


def test_price_decreases_as_expiry_approaches():
    price_day_5 = calculate_reservation_price(
        initial_price=100,
        minimum_price=60,
        remaining_shelf_life_days=5,
        total_shelf_life_days=5,
    )

    price_day_2 = calculate_reservation_price(
        initial_price=100,
        minimum_price=60,
        remaining_shelf_life_days=2,
        total_shelf_life_days=5,
    )

    assert price_day_2 < price_day_5