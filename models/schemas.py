
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# The agents in our simulation
class AgentType(str, Enum):
    DISTRIBUTOR = "distributor"
    RETAILER_A = "retailer_a"
    RETAILER_B = "retailer_b"


# Possible actions an agent can take
class ActionType(str, Enum):
    OFFER = "offer"
    ACCEPT = "accept"
    REJECT = "reject"
    WALK_AWAY = "walk_away"


# Information about the market
class MarketState(BaseModel):
    day: int
    product_name: str
    available_quantity: int
    remaining_shelf_life_days: int
    distributor_reservation_price: float


# Information about each retailer
class RetailerState(BaseModel):
    retailer_id: AgentType
    capacity: int
    current_inventory: int
    sales_velocity: float
    max_willingness_to_pay: float
    minimum_shelf_life_days: int
    budget: float

    @property
    def available_capacity(self) -> int:
        return max(0, self.capacity - self.current_inventory)


# A proposed deal between the distributor and a retailer
class Offer(BaseModel):
    seller_id: AgentType
    buyer_id: AgentType
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    minimum_remaining_shelf_life_days: int = Field(ge=0)


# An agent's decision
class Decision(BaseModel):
    agent_id: AgentType
    action: ActionType
    offer: Optional[Offer] = None
    reason: str = ""


# Result after an offer is processed
class DealResult(BaseModel):
    accepted: bool
    quantity: int
    unit_price: float
    total_cost: float
    message: str
