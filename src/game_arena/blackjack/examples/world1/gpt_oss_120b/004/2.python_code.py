
from functools import lru_cache

# Full deck of ranks
FULL_DECK = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

# Card values (except Ace which is handled specially)
CARD_VALUE = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10,
}

def hand_value(hand: list[str], target: int) -> int:
    """
    Compute the best possible hand total not exceeding target,
    treating Aces as 11 or 1 as needed.
    """
    total = 0
    ace_count = 0
    for card in hand:
        if card == "A":
            ace_count += 1
            total += 11
        else:
            total += CARD_VALUE[card]

    # Downgrade Aces from 11 to 1 while we are over the target
    while total > target and ace_count:
        total -= 10   # 11 -> 1
        ace_count -= 1
    return total

def bust_probability(hand: list[str], target: int) -> float:
    """
    Return the probability that the next drawn card will bust the hand.
    """
    remaining = [c for c in FULL_DECK if c not in hand]
    if not remaining:
        return 1.0  # no cards left, forced bust if we try to hit

    busts = 0
    for card in remaining:
        new_hand = hand + [card]
        if hand_value(new_hand, target) > target:
            busts += 1
    return busts / len(remaining)

def policy(hand: list[str], target: int) -> str:
    """
    Decide whether to HIT or STAY.

    - Stay if we have already reached the target.
    - Stay if the chance of busting on the next draw is >= 50%.
    - Otherwise hit.
    """
    current_total = hand_value(hand, target)

    # If we are already at the target, staying is optimal.
    if current_total == target:
        return "STAY"

    # If we have busted (should not happen during normal play), stay.
    if current_total > target:
        return "STAY"

    # Compute bust risk for the next card.
    prob_bust = bust_probability(hand, target)

    # Stay when the risk is too high.
    if prob_bust >= 0.5:
        return "STAY"
    else:
        return "HIT"
