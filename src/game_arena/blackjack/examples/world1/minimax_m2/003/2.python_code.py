
from typing import List

# All possible ranks in a single‑suit deck
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Base card values (Ace is treated as 11 for the moment; the special rule
# is applied later)
BASE_VALUE = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}


def _hand_value(hand: List[str], target: int) -> int:
    """
    Compute the value of `hand` according to the problem statement.
    Ace is counted as 11 unless that makes the total exceed `target`,
    in which case it is counted as 1.
    """
    total = 0
    has_ace = False
    for c in hand:
        if c == "A":
            has_ace = True
        else:
            total += BASE_VALUE[c]

    if has_ace:
        total += 11               # initial Ace value
        if total > target:        # bust – turn Ace into 1
            total -= 10
    return total


def policy(hand: List[str], target: int) -> str:
    """
    Decide whether to HIT or STAY.

    Parameters
    ----------
    hand : List[str]
        The cards currently held by the player.
    target : int
        The fixed target score T for this game.

    Returns
    -------
    str
        "HIT" or "STAY".
    """
    # If the deck is exhausted we cannot draw any more cards.
    if len(hand) == len(RANKS):
        return "STAY"

    # Current hand value
    cur_sum = _hand_value(hand, target)

    # Cards that are still unseen (the remaining deck)
    remaining = [r for r in RANKS if r not in set(hand)]

    # Count how many of those cards would bust the hand.
    bust_count = 0
    for r in remaining:
        new_sum = _hand_value(hand + [r], target)
        if new_sum > target:
            bust_count += 1

    bust_prob = bust_count / len(remaining)

    # Decision rule: hit only when the bust probability is small.
    # The threshold (0.15) is a conservative safety margin.
    if bust_prob <= 0.15:
        return "HIT"
    else:
        return "STAY"
