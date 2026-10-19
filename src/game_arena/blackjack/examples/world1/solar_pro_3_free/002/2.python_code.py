
import numpy as np
from typing import List

# Full deck of 13 distinct cards
FULL_DECK = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Mapping card values for base calculation (Ace counts as 1 here for min value)
CARD_VALUES = {
    'A': 1,  # used in min value calculation; actual Ace value depends on condition
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10
}

def _compute_hand_value(hand: List[str], target: int) -> int:
    """
    Calculate the maximum valid hand value <= target.
    Uses Ace=11 if possible, else Ace=1. Assumes hand is bust-free.
    """
    sum_base = sum(CARD_VALUES[card] for card in hand)
    ace_count = hand.count('A')
    
    # If we have an Ace, determine optimal count
    if ace_count > 0:
        if sum_base + 11 <= target:
            return sum_base + 11
        elif sum_base + 1 <= target:
            return sum_base + 1
        else:
            # This should never happen in valid states (would indicate bust)
            return None  # Signal bust (should not occur)
    
    # No Ace: value is just sum (must be <= target in valid states)
    return sum_base

def policy(hand: List[str], target: int) -> str:
    """
    Return 'HIT' or 'STAY' based on adaptive evaluation.
    
    Strategy:
    - Hit if expected safe hand value after hit > current hand value.
    - Prioritize hitting when we can reach target exactly (perfect hand).
    - Avoid hitting if current hand value == target or all next cards bust.
    """
    # Current hand value (must be <= target by game rules)
    current_val = _compute_hand_value(hand, target)
    
    # If we're already at target, hitting will either bust or decrease value
    if current_val == target:
        return "STAY"
    
    # Cards remaining in our deck (unique since one copy per rank)
    remaining_cards = [card for card in FULL_DECK if card not in hand]
    n_remain = len(remaining_cards)
    
    # If no cards left, must stay
    if n_remain == 0:
        return "STAY"
    
    # Evaluate all possible next cards
    safe_values = []
    for card in remaining_cards:
        new_hand = hand + [card]
        
        # Calculate new hand value
        sum_base = sum(CARD_VALUES[c] for c in new_hand)
        ace_in_hand = 'A' in new_hand
        
        if ace_in_hand:
            if sum_base + 11 <= target:
                new_val = sum_base + 11
            elif sum_base + 1 <= target:
                new_val = sum_base + 1
            else:
                continue  # Bust (ignore in safe values)
        else:
            new_val = sum_base  # Must be <= target in valid states
        
        if new_val <= target:
            safe_values.append(new_val)
    
    # If all next cards bust, stay
    if not safe_values:
        return "STAY"
    
    # Best safe outcome
    best_safe = max(safe_values)
    
    # If best safe outcome isn't better than current, no point hitting
    if best_safe <= current_val:
        return "STAY"
    
    # Check if we can hit to exactly reach target (ideal outcome)
    if best_safe == target:
        return "HIT"
    
    # Calculate expected safe hand value
    expected_safe = np.mean(safe_values)
    
    # Compare hit utility vs staying (current_val)
    # Hit utility = probability_of_safe * expected_safe
    safe_count = len(safe_values)
    hit_utility = (safe_count / n_remain) * expected_safe
    
    return "HIT" if hit_utility > current_val else "STAY"
