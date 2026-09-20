
def calculate_reservation_price(
    initial_price: float,
    minimum_price: float,
    remaining_shelf_life_days: int,
    total_shelf_life_days: int,
) -> float:
    """
    Calculate the distributor's minimum acceptable price.

    The price decreases linearly as the product approaches expiry.
    """

    if initial_price <= 0:
        raise ValueError("Initial price must be positive.")

    if minimum_price < 0:
        raise ValueError("Minimum price cannot be negative.")

    if minimum_price > initial_price:
        raise ValueError("Minimum price cannot exceed initial price.")

    if total_shelf_life_days <= 0:
        raise ValueError("Total shelf life must be positive.")

    if remaining_shelf_life_days < 0:
        raise ValueError("Remaining shelf life cannot be negative.")

    if remaining_shelf_life_days > total_shelf_life_days:
        raise ValueError(
            "Remaining shelf life cannot exceed total shelf life."
        )

    # Fraction of shelf life remaining
    remaining_fraction = (
        remaining_shelf_life_days / total_shelf_life_days
    )

    # Price falls as the product approaches expiry
    price = minimum_price + (
        initial_price - minimum_price
    ) * remaining_fraction

    return round(price, 2)
