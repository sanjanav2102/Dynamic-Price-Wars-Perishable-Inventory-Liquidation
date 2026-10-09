"""
Prompt builders for LLM-assisted negotiation.
"""

import json

from models.schemas import (
    MarketState,
    RetailerState,
    Offer,
)


def _json(data) -> str:
    """
    Convert Pydantic models into JSON safely.
    """

    if hasattr(data, "model_dump"):
        data = data.model_dump(
            mode="json"
        )

    return json.dumps(
        data,
        indent=2,
    )


def retailer_initial_offer_prompt(
    retailer_role: str,
    market_state: MarketState,
    retailer_state: RetailerState,
) -> str:
    """
    Prompt for creating an initial retailer offer.
    """

    return f"""
You are the {retailer_role} in a perishable inventory
price negotiation.

Your objective is to purchase inventory while respecting
your own business constraints.

CURRENT MARKET:
{_json(market_state)}

YOUR RETAILER STATE:
{_json(retailer_state)}

RULES:
1. Do not exceed your storage capacity.
2. Do not exceed your budget.
3. Do not exceed your maximum willingness to pay.
4. Respect your minimum shelf-life requirement.
5. Consider remaining market inventory.
6. Consider the remaining shelf life.
7. Choose a realistic quantity.
8. Choose a realistic price.
9. Your seller must be "distributor".
10. Your buyer must be "{retailer_state.retailer_id}".

For the initial decision:
- action should normally be "counter".
- provide an offer.
- provide a short reason.

Return only the structured Decision JSON.
"""


def retailer_response_prompt(
    retailer_role: str,
    market_state: MarketState,
    retailer_state: RetailerState,
    incoming_offer: Offer,
) -> str:
    """
    Prompt for responding to a distributor offer.
    """

    return f"""
You are the {retailer_role} in a perishable inventory
negotiation.

Your objective is to maximize the usefulness of the purchase
while respecting your constraints.

CURRENT MARKET:
{_json(market_state)}

YOUR RETAILER STATE:
{_json(retailer_state)}

CURRENT DISTRIBUTOR OFFER:
{_json(incoming_offer)}

DECISION OPTIONS:
- accept
- counter
- walk_away

RULES:
1. Never exceed your maximum willingness to pay.
2. Never exceed your available storage capacity.
3. Never exceed your remaining budget.
4. Respect minimum shelf-life requirements.
5. Consider remaining distributor inventory.
6. Consider remaining shelf life.
7. If the offer is acceptable, accept it.
8. If the offer is too expensive but negotiation is useful,
   counter with a realistic offer.
9. If no acceptable deal is possible, walk away.
10. The buyer must remain "{retailer_state.retailer_id}".
11. The seller must remain "distributor".

If action is "accept", include the current offer.
If action is "counter", include a valid counteroffer.
If action is "walk_away", an offer is not required.

Return only the structured Decision JSON.
"""


def distributor_response_prompt(
    market_state: MarketState,
    incoming_offer: Offer,
) -> str:
    """
    Prompt for distributor decision.
    """

    return f"""
You are the distributor selling perishable inventory.

Your objective is to obtain a reasonable price while
reducing the risk of inventory expiring unsold.

CURRENT MARKET:
{_json(market_state)}

CURRENT RETAILER OFFER:
{_json(incoming_offer)}

DECISION OPTIONS:
- accept
- counter
- reject

RULES:
1. Never accept a price below the current reservation price.
2. Do not sell more units than are available.
3. Consider remaining shelf life.
4. As expiry approaches, becoming more flexible is reasonable.
5. Preserve the incoming buyer ID.
6. Preserve the seller ID "distributor".
7. Keep quantity realistic.
8. If the offer is acceptable, accept it.
9. If the price is too low but negotiation is useful, counter.
10. If no acceptable transaction is possible, reject.

If action is "accept", include the current offer.
If action is "counter", provide a valid counteroffer.
If action is "reject", an offer is not required.

Return only the structured Decision JSON.
"""