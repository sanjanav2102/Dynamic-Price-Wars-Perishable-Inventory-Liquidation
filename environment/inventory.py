
class InventoryManager:
    def __init__(self, initial_quantity: int):
        if initial_quantity < 0:
            raise ValueError("Initial quantity cannot be negative.")

        self.initial_quantity = initial_quantity
        self.available_quantity = initial_quantity
        self.sold_quantity = 0
        self.expired_quantity = 0

    # Compatibility properties for tests and integration code
    @property
    def remaining_inventory(self) -> int:
        return self.available_quantity

    @property
    def expired_inventory(self) -> int:
        return self.expired_quantity

    def has_stock(self, quantity: int) -> bool:
        return 0 <= quantity <= self.available_quantity

    def can_sell(self, quantity: int) -> bool:
        return self.has_stock(quantity)

    def sell(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Sale quantity must be positive.")

        if quantity > self.available_quantity:
            raise ValueError("Not enough stock available.")

        self.available_quantity -= quantity
        self.sold_quantity += quantity

    def expire_remaining_stock(self) -> int:
        expired = self.available_quantity
        self.expired_quantity += expired
        self.available_quantity = 0
        return expired

    def expire_all_remaining(self) -> int:
        return self.expire_remaining_stock()

    def expire_quantity(self, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Expiry quantity must be positive.")

        if quantity > self.available_quantity:
            raise ValueError("Cannot expire more stock than available.")

        self.available_quantity -= quantity
        self.expired_quantity += quantity

    def get_state(self) -> dict:
        return {
            "initial_quantity": self.initial_quantity,
            "available_quantity": self.available_quantity,
            "sold_quantity": self.sold_quantity,
            "expired_quantity": self.expired_quantity,
        }
