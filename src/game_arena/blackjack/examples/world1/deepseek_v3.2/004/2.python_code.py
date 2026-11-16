
import random
from typing import List

def card_value(card: str, current_total: int, target: int) -> int:
    """Return the value of a single card given current total and target."""
    if card == "A":
        return 11 if current_total + 11 <= target else 1
    elif card in ("J", "Q", "K"):
        return 10
    else:
        return int(card)

def hand_value(hand: List[str], target: int) -> int:
    """Calculate total value of hand, optimizing Aces."""
    total = 0
    aces = 0
    for card in hand:
        if card == "A":
            aces += 1
        elif card in ("J", "Q", "K"):
            total += 10
        else:
            total += int(card)
    # Add aces optimally
    for _ in range(aces):
        if total + 11 <= target:
            total += 11
        else:
            total += 1
    return total

def policy(hand: List[str], target: int) -> str:
    """
    Policy for the simplified Blackjack game.
    Returns "HIT" or "STAY".
    """
    # All possible cards in a deck
    full_deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    
    # Cards remaining in our deck (cards not yet drawn)
    remaining = [c for c in full_deck if c not in hand]
    
    # Current hand value
    current = hand_value(hand, target)
    
    # If we are already at or above target, staying is safe
    if current >= target:
        return "STAY"
    
    # Calculate bust probability if we draw one more card
    bust_count = 0
    for card in remaining:
        # Value of this card given our current total
        card_val = card_value(card, current, target)
        new_total = current + card_val
        if new_total > target:
            bust_count += 1
    
    bust_prob = bust_count / len(remaining) if remaining else 0
    
    # Heuristic decision
    if bust_prob > 0.3:
        return "STAY"
    
    # If we are far below target, hit
    if current < target - 7:
        return "HIT"
    
    # If we are moderately below target, consider expected improvement
    # Compute average value of remaining cards (conservative: treat Ace as 1)
    avg_value = sum(card_value(c, 0, target) if c != "A" else 1 for c in remaining) / len(remaining) if remaining else 0
    if current + avg_value <= target:
        return "HIT"
    else:
        return "STAY"
