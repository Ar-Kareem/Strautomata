
from typing import List

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
VALUE_MAP = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10
}

def best_total_for(hand: List[str], target: int) -> int:
    """
    Compute the best numeric total for a hand given the target T.
    Aces are treated as 11 where possible without exceeding target; otherwise as 1.
    If no configuration gets <= target, returns the smallest possible total (all A as 1).
    """
    aces = hand.count("A")
    total = sum(VALUE_MAP[r] for r in hand if r != "A")
    total += 11 * aces
    # Try to reduce Aces from 11->1 (i.e., subtract 10) until <= target or no aces left
    while total > target and aces > 0:
        total -= 10
        aces -= 1
    return total

def remaining_deck(hand: List[str]) -> List[str]:
    """
    Return list of ranks remaining in the player's deck (one copy of each rank originally).
    Removes ranks present in hand (each rank appears at most once in hand).
    """
    # since there's exactly one copy of each rank in the deck
    remaining = []
    hand_counts = {}
    for r in hand:
        hand_counts[r] = hand_counts.get(r, 0) + 1
    for r in RANKS:
        # include rank if not already used in hand
        if hand_counts.get(r, 0) == 0:
            remaining.append(r)
    return remaining

def policy(hand: List[str], target: int) -> str:
    """
    Decision policy: compare expected distance-to-target after drawing one more card
    (with a heavy penalty for busting) to current distance. If expected distance is
    smaller, decide to HIT; otherwise STAY.
    """
    # Defensive: if already exactly at target, no need to hit.
    cur_total = best_total_for(hand, target)
    if cur_total >= target:
        # If equal to target, stay; if cur_total > target (already busted), stay (though game over).
        return "STAY"
    cur_distance = target - cur_total

    deck = remaining_deck(hand)
    if not deck:
        return "STAY"

    # Set a large penalty for bust to strongly discourage busts
    bust_penalty = target + 20

    total_distance = 0.0
    for card in deck:
        new_hand = hand + [card]
        new_total = best_total_for(new_hand, target)
        if new_total > target:
            total_distance += bust_penalty
        else:
            total_distance += (target - new_total)
    expected_distance = total_distance / len(deck)

    # If expected distance by hitting is strictly better (smaller), then HIT
    if expected_distance < cur_distance:
        return "HIT"
    else:
        return "STAY"
