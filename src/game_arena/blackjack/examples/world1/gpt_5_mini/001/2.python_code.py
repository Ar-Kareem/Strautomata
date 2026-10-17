
from typing import List

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

# Compute best hand value with flexible aces (some Aces counted as 11 or 1)
def compute_hand_value(hand: List[str], target: int) -> int:
    non_ace_sum = 0
    aces = 0
    for c in hand:
        if c == "A":
            aces += 1
        else:
            non_ace_sum += VALUE_MAP.get(c, 0)
    # Start by treating all aces as 11
    total = non_ace_sum + 11 * aces
    # Reduce aces from 11 to 1 (subtract 10) while total > target and we have aces counted as 11
    # This tries to maximize total while keeping it <= target when possible.
    aces_as_11 = aces
    while total > target and aces_as_11 > 0:
        total -= 10  # convert one ace from 11 to 1
        aces_as_11 -= 1
    return total

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to "HIT" or "STAY" given current hand and target.
    Strategy:
      - Compute current hand value with flexible aces (favor 11s when possible).
      - For each remaining rank in our personal 13-card deck (one copy each rank),
        compute resulting hand value if that card is drawn.
      - Define a penalty: distance = abs(target - value) for non-bust hands; a large
        penalty for busts. Compute expected penalty over remaining cards.
      - If expected penalty after HIT is less than current distance, return "HIT",
        otherwise return "STAY".
    """
    # Defensive: if already busted or exactly at target, prefer STAY (no benefit hitting).
    current_value = compute_hand_value(hand, target)
    # If already busted, nothing to do; STAY (policy must return something)
    if current_value > target:
        return "STAY"
    # If exactly target, best to STAY.
    if current_value == target:
        return "STAY"

    # Determine remaining ranks in our personal deck (one of each rank, those not yet in hand)
    remaining = [r for r in RANKS if r not in hand]
    if not remaining:
        return "STAY"

    # Current penalty is the distance to target
    current_penalty = abs(target - current_value)

    # Large penalty for busts (bigger than any possible distance, target up to 30 -> max distance 30)
    BUST_PENALTY = 1000.0

    total_penalty = 0.0
    for r in remaining:
        new_hand = hand + [r]
        new_value = compute_hand_value(new_hand, target)
        if new_value > target:
            penalty = BUST_PENALTY
        else:
            penalty = abs(target - new_value)
        total_penalty += penalty
    expected_penalty = total_penalty / len(remaining)

    # If expected penalty by hitting is strictly lower than current penalty, HIT; otherwise STAY.
    if expected_penalty < current_penalty:
        return "HIT"
    else:
        return "STAY"
