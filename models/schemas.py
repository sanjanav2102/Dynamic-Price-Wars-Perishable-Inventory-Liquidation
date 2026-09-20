
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, AliasChoices, ConfigDict

class AgentType(str, Enum):
    DISTRIBUTOR = "distributor"

    # Existing retailer names
    RETAILER_A = "retailer_a"
    RETAILER_B = "retailer_b"

    # Names expected by the agents and tests
    PREMIUM_RETAILER = "premium_retailer"
    BUDGET_RETAILER = "budget_retailer"

class ActionType(str, Enum):
    OFFER = "offer"
    COUNTER = "counter"
    ACCEPT = "accept"
    REJECT = "reject"
    WALK_AWAY = "walk_away"


class MarketState(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    day: int = 1
    product_name: str = "Fresh Milk"

    available_quantity: int = Field(
        default=0,
        validation_alias=AliasChoices(
            "available_quantity",
            "remaining_inventory",
            "total_inventory",
        ),
    )

    remaining_shelf_life_days: int = 0

    total_shelf_life_days: int = 0
    total_inventory: int = 0

    distributor_reservation_price: float

    round_number: int = 1

    @property
    def remaining_inventory(self) -> int:
        return self.available_quantity


class RetailerState(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    retailer_id: str
    retailer_type: Optional[AgentType] = None

    capacity: int = Field(
        validation_alias=AliasChoices(
            "capacity",
            "storage_capacity",
        )
    )

    current_inventory: int = 0

    sales_velocity: float = Field(
        validation_alias=AliasChoices(
            "sales_velocity",
            "sales_velocity_per_day",
        )
    )

    max_willingness_to_pay: float

    minimum_shelf_life_days: int = Field(
        validation_alias=AliasChoices(
            "minimum_shelf_life_days",
            "minimum_required_shelf_life_days",
        )
    )

    budget: float

    @property
    def available_capacity(self) -> int:
        return max(
            0,
            self.capacity - self.current_inventory,
        )

    @property
    def storage_capacity(self) -> int:
        return self.capacity

    @property
    def sales_velocity_per_day(self) -> float:
        return self.sales_velocity

    @property
    def minimum_required_shelf_life_days(self) -> int:
        return self.minimum_shelf_life_days


class Offer(BaseModel):
    # Accept either name when creating an Offer.
    # Internally, price_per_unit is the canonical field.
    model_config = ConfigDict(populate_by_name=True)

    seller_id: str
    buyer_id: str
    quantity: int = Field(gt=0)

    price_per_unit: float = Field(
        gt=0,
        validation_alias=AliasChoices("price_per_unit", "unit_price"),
    )

    minimum_remaining_shelf_life_days: int = Field(ge=0)

    # Keep existing environment code using offer.unit_price working.
    @property
    def unit_price(self) -> float:
        return self.price_per_unit


class Decision(BaseModel):
    agent_id: Optional[AgentType] = None
    action: ActionType
    offer: Optional[Offer] = None
    reason: str = ""


class DealResult(BaseModel):
    accepted: bool = False
    quantity: int = 0
    unit_price: float = 0.0
    total_cost: float = 0.0
    message: str = ""

    @property
    def success(self) -> bool:
        return self.accepted

    @property
    def price_per_unit(self) -> float:
        return self.unit_price
    @property
    def total_value(self) -> float:
       """Compatibility alias for total_cost."""
       return self.total_cost

class NegotiationEvent(BaseModel):
    round_number: int
    turn_number: int
    actor: str
    action: ActionType
    price_per_unit: Optional[float] = None
    quantity: Optional[int] = None
    minimum_remaining_shelf_life_days: Optional[int] = None
    reason: str = ""


class NegotiationResult(BaseModel):
    success: bool
    buyer_id: str
    seller_id: str
    final_offer: Optional[Offer] = None
    deal_result: Optional[DealResult] = None
    turns_used: int
    events: List[NegotiationEvent] = Field(default_factory=list)
    reason: str = ""
