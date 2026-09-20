from abc import ABC, abstractmethod

from models.schemas import (
    MarketState,
    RetailerState,
    Offer,
    Decision,
    ActionType,
)


class BaseAgent(ABC):

    def __init__(
        self,
        agent_id: str,
    ):
        self.agent_id = agent_id

    @abstractmethod
    def respond_to_offer(
        self,
        offer: Offer,
        market_state: MarketState,
    ) -> Decision:
        pass