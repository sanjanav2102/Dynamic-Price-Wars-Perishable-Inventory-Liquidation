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
7. If the incoming offer satisfies all business constraints, accept it.
8. If the incoming offer is unacceptable but a mutually acceptable price and affordable positive quantity exist, prefer a realistic counteroffer over walking away.
9. Walk away only when no feasible purchase or valid counteroffer exists under the stated price, budget, capacity, inventory, and freshness constraints.
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
    """Prompt for distributor decision."""

    return f"""
You are the distributor selling perishable inventory.

Your goal is to maximize revenue while selling inventory
before it expires.

CURRENT MARKET:
{_json(market_state)}

CURRENT RETAILER OFFER:
{_json(incoming_offer)}

DECISION OPTIONS:
- accept
- counter
- reject

MANDATORY BUSINESS RULES:
1. Never accept a price below the current distributor reservation price.
2. Never offer more units than the available inventory.
3. Preserve the incoming buyer ID.
4. The seller ID must remain "distributor".
5. Keep price and quantity positive.
6. Never invent market facts or retailer budget information.

NEGOTIATION STRATEGY:
1. Calculate the price gap between the incoming offer and the
   distributor reservation price.
2. If the incoming offer meets or exceeds the reservation price,
   accept it unless another mandatory constraint is violated.
3. If the offer is below the reservation price, counter at a price
   that is at least the reservation price.
4. When shelf life is short, prefer a reasonable counteroffer that
   encourages a deal instead of holding out for a high price.
5. Avoid repeating the same price in consecutive counteroffers.
6. Keep the incoming quantity unless it exceeds available inventory.
7. Do not claim a deal has succeeded unless the environment accepts it.

RESPONSE FORMAT:
- For "accept", include the incoming offer.
- For "counter", include a valid offer object.
- For "reject", an offer is not required.
- Give a brief reason explaining the decision.

Return only the structured Decision JSON.
"""
