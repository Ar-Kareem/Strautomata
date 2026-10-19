
from typing import List

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "A": 11,  # initial value; may be treated as 1 by adjustment
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

def hand_value(cards: List[str], target: int) -> int:
    """
    Compute the best total for 'cards' given the target.
    Treat Aces as 11 where possible without exceeding target, otherwise as 1.
    If no arrangement keeps total <= target, return the minimal possible total (some Aces as 1).
    """
    total = 0
    aces = 0
    for c in cards:
        if c == "A":
            aces += 1
            total += 11
        else:
            total += VALUE_MAP[c]
    # Reduce aces from 11 to 1 (subtract 10) as needed to try to get <= target
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to "HIT" or "STAY".
    Uses a one-step lookahead on the known remaining cards in our 13-card deck.
    """
    # Defensive copy
    hand = list(hand)
    # Current total
    cur_total = hand_value(hand, target)
    # If already busted, nothing to do (we've already lost). Return STAY.
    if cur_total > target:
        return "STAY"
    # Build remaining ranks in our deck (one copy of each of RANKS minus what's in hand)
    remaining = [r for r in RANKS if r not in hand]
    if not remaining:
        return "STAY"
    # Distance if we stay now
    stay_distance = target - cur_total  # >= 0
    # Define a large penalty for a bust (worse than any non-bust distance)
    bust_penalty = target + 50
    # Compute expected distance after drawing one card (and then staying)
    total_distance = 0.0
    for r in remaining:
        # Evaluate new hand
        new_hand = hand + [r]
        new_total = hand_value(new_hand, target)
        if new_total > target:
            dist = bust_penalty
        else:
            dist = target - new_total
        total_distance += dist
    expected_distance_if_hit = total_distance / len(remaining)
    # Choose action that minimizes expected distance to target
    if expected_distance_if_hit < stay_distance:
        return "HIT"
    else:
        return "STAY"

# If run as a script, provide a simple self-check (not required by the arena).
if __name__ == "__main__":
    # Quick manual tests
    print(policy(["10"], 21))  # likely HIT (single card 10 vs 21)
    print(policy(["10", "9"], 21))  # likely STAY (19 vs 21)
    print(policy(["A", "9"], 21))  # A(11)+9=20 -> STAY
    print(policy(["A", "K"], 21))  # 21 -> STAY
