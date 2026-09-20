'''This defines the rules.'''
''' 
BASE IMPLEMENTATION
Retailer makes offer
       ↓
Distributor evaluates
       ↓
Accept?
  Yes → Deal
  No  → Counter
       ↓
Retailer evaluates
       ↓
Accept?
  Yes → Deal
  No  → Counter
       ↓
Maximum turns reached?
       ↓
End negotiation

'''
MAX_NEGOTIATION_TURNS = 6

NEGOTIATION_TURN_ORDER = [
    "retailer",
    "distributor",
]