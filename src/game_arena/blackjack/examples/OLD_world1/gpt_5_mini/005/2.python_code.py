
from typing import List

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "A": 11,  # handled specially
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10
}

def _hand_value_and_bust(hand: List[str], target: int) -> (int, bool):
    """
    Compute the best hand value according to the game's Ace rule:
    - Aces can count as 11 *only if* the resulting hand value is <= target.
    - Otherwise Aces count as 1.
    We return (value, is_bust) where is_bust is True iff minimal value (all aces=1)
    is > target.
    """
    # Count aces separately
    aces = 0
    total = 0
    for c in hand:
        if c == "A":
            aces += 1
            total += 1  # count ace as 1 initially
        else:
            total += VALUE_MAP.get(c, 0)
    # minimal total with all aces as 1
    min_total = total
    if min_total > target:
        return min_total, True
    # try to upgrade some aces from 1 to 11 (i.e., add 10 per ace) while <= target
    # add as many as possible to maximize hand value without exceeding target
    for _ in range(aces):
        if total + 10 <= target:
            total += 10
        else:
            break
    return total, False

def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to HIT or STAY.
    Heuristic: perform a one-step lookahead minimizing expected absolute distance to target.
    If hitting (drawing one card uniformly among remaining ranks in our deck) yields a
    strictly lower expected distance than staying now, return "HIT". Otherwise "STAY".
    Busts are heavily penalized in the distance metric.
    """
    # Defensive: if current hand already bust (shouldn't happen in normal flow), STAY
    current_value, current_bust = _hand_value_and_bust(hand, target)
    if current_bust:
        return "STAY"

    # Current distance to target
    current_distance = abs(target - current_value)
    if current_distance == 0:
        return "STAY"

    # Build remaining ranks in our deck (one of each rank initially, remove those in hand)
    remaining = []
    # We consider that each rank appears once in the deck; if hand contains a rank,
    # that rank is no longer available to draw.
    for r in RANKS:
        if hand.count(r) == 0:
            remaining.append(r)

    if not remaining:
        return "STAY"

    # Large penalty for busting to discourage risky draws
    bust_penalty = target + 100

    # Compute expected distance after one draw (and then stopping)
    total_distance = 0.0
    for r in remaining:
        new_hand = hand + [r]
        v, b = _hand_value_and_bust(new_hand, target)
        if b:
            dist = bust_penalty
        else:
            dist = abs(target - v)
        total_distance += dist

    expected_distance = total_distance / len(remaining)

    # If expected distance strictly improves by hitting, then HIT
    if expected_distance < current_distance:
        return "HIT"
    else:
        return "STAY"
