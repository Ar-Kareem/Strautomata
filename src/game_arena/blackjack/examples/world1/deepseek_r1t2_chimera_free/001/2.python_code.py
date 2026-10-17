
import numpy as np

def policy(hand: list[str], target: int) -> str:
    total = 0
    aces = 0
    
    # Calculate total for non-Ace cards and count Aces
    for card in hand:
        if card == "A":
            aces += 1
        elif card in ["J", "Q", "K"]:
            total += 10
        else:
            total += int(card)
    
    # Optimally add Aces (11 if possible, else 1)
    for _ in range(aces):
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    
    # Decision logic
    if total >= target:
        return "STAY"
    if total + 10 <= target:
        return "HIT"
    else:
        return "STAY"
