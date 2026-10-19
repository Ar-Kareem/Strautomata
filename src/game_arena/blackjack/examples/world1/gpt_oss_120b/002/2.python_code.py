
"""Blackjack‑like policy for a random target T (10‑30).

The function `policy(hand, target)` returns either "HIT" or "STAY".
"""

from typing import List

# fixed list of ranks in the deck
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# static value mapping (Ace handled specially later)
VALUE_MAP = {
    "A": 11,   # will be reduced to 1 if needed
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10,
}


def hand_total(hand: List[str], target: int) -> int:
    """Return the best total for *hand* using flexible Ace values.
    The result may be > target (bust) if even the minimal Ace adjustment cannot
    bring the sum down.
    """
    total = sum(VALUE_MAP[c] for c in hand)
    ace_count = hand.count("A")
    # downgrade Aces from 11 to 1 while we are over the target and still have Aces to downgrade
    while total > target and ace_count > 0:
        total -= 10          # 11 -> 1
        ace_count -= 1
    return total


def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to draw another card ("HIT") or stop ("STAY").

    Parameters
    ----------
    hand : list[str]
        Cards currently held.
    target : int
        The target score T (10 ≤ T ≤ 30).

    Returns
    -------
    str
        "HIT" or "STAY".
    """
    # Current hand evaluation
    cur_total = hand_total(hand, target)

    # If we have already busted (should not happen in normal play) we stay.
    if cur_total > target:
        return "STAY"

    # No cards left to draw – must stay
    remaining_cards = [r for r in RANKS if r not in hand]
    n_remain = len(remaining_cards)
    if n_remain == 0:
        return "STAY"

    # Current distance to the target (the smaller, the better)
    cur_dist = target - cur_total

    # Compute bust probability and expected distance after a single extra draw
    bust_prob = 0.0
    exp_dist = 0.0  # weighted by probability of non‑bust outcomes
    for card in remaining_cards:
        # simulate drawing this card
        new_hand = hand + [card]
        new_total = hand_total(new_hand, target)

        if new_total > target:
            bust_prob += 1.0 / n_remain
        else:
            # distance after the draw (we will stay after this draw)
            exp_dist += (target - new_total) / n_remain

    # Decision logic
    # 1. If bust risk is high, stay.
    if bust_prob > 0.35:
        return "STAY"

    # 2. If expected distance improves, hit.
    if exp_dist < cur_dist:
        return "HIT"

    # 3. Otherwise stay.
    return "STAY"
