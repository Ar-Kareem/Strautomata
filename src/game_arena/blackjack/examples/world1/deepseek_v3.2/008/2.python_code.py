
import numpy as np

def policy(hand: list[str], target: int) -> str:
    # All possible cards in one suit
    all_cards = {"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
    
    # Compute current hand value
    def card_value(card: str, current_sum: int, target: int) -> int:
        if card == "A":
            return 11 if current_sum + 11 <= target else 1
        elif card in ("J", "Q", "K"):
            return 10
        else:
            return int(card)
    
    s = 0
    for card in hand:
        s += card_value(card, s, target)
    
    # If we are already at target, stop
    if s == target:
        return "STAY"
    
    # Determine which cards remain in our deck
    remaining = list(all_cards - set(hand))
    n_remaining = len(remaining)
    if n_remaining == 0:
        return "STAY"
    
    # Compute for each remaining card its value and whether it would cause a bust
    bust_count = 0
    value_sum = 0
    for card in remaining:
        v = card_value(card, s, target)
        value_sum += v
        if s + v > target:
            bust_count += 1
    
    bust_prob = bust_count / n_remaining
    expected_new_sum = s + value_sum / n_remaining
    
    # Heuristic decision
    # If we are far below target, hit aggressively
    if s <= target - 10:
        return "HIT"
    
    # Otherwise, hit only if bust probability is not too high and expected new sum is not worse
    if bust_prob < 0.5 and expected_new_sum <= target:
        return "HIT"
    else:
        return "STAY"
