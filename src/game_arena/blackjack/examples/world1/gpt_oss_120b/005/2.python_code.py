
import random
from collections import Counter

# ----------------------------------------------------------------------
# Card utilities
# ----------------------------------------------------------------------
CARD_VALUES = {
    "A": 11,  # special handling later
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}
ALL_RANKS = list(CARD_VALUES.keys())

def hand_value(hand, target):
    """Return the best Blackjack‑like value of *hand* with respect to *target*."""
    total = 0
    aces = 0
    for c in hand:
        if c == "A":
            aces += 1
        else:
            total += CARD_VALUES[c]
    # count each ace as 11 first
    total += aces * 11
    # downgrade aces to 1 while we are over the target
    while total > target and aces:
        total -= 10   # turn one ace from 11 -> 1
        aces -= 1
    return total

def is_bust(hand, target):
    return hand_value(hand, target) > target

# ----------------------------------------------------------------------
# Opponent model (simple aggressive baseline)
# ----------------------------------------------------------------------
def opponent_play(target, rng):
    """Simulate one opponent round using the baseline policy."""
    deck = ALL_RANKS.copy()
    opponent_hand = []
    while True:
        value = hand_value(opponent_hand, target)
        # baseline: hit while we are at least 2 points below the target
        if value <= target - 2 and deck:
            card = rng.choice(deck)
            opponent_hand.append(card)
            deck.remove(card)
        else:
            break
        if is_bust(opponent_hand, target):
            break
    return opponent_hand

# ----------------------------------------------------------------------
# Win‑rate estimation utilities
# ----------------------------------------------------------------------
def win_against_opponent(my_hand, target, rng, simulations=300):
    """Return estimated probability of my_hand winning against the baseline opponent."""
    my_val = hand_value(my_hand, target)
    my_bust = my_val > target
    if my_bust:
        return 0.0  # bust loses (draw case ignored for simplicity)

    wins = 0
    for _ in range(simulations):
        opp_hand = opponent_play(target, rng)
        opp_val = hand_value(opp_hand, target)
        opp_bust = opp_val > target

        if opp_bust:
            wins += 1
        else:
            # closer to target wins; ties are not wins
            my_dist = target - my_val
            opp_dist = target - opp_val
            if my_dist < opp_dist:
                wins += 1
    return wins / simulations

def expected_win_after_hit(hand, target, rng, simulations=300):
    """Expected win probability if we draw one more card now."""
    # cards still in our personal deck
    remaining = [c for c in ALL_RANKS if c not in hand]
    if not remaining:
        # no cards left – we must stay
        return win_against_opponent(hand, target, rng, simulations)

    total_prob = 0.0
    for card in remaining:
        prob = 1.0 / len(remaining)  # uniform because each rank occurs once
        new_hand = hand + [card]
        if is_bust(new_hand, target):
            # bust → loss (opponent may also bust, but that is rare;
            # we treat it as a loss for a conservative estimate)
            win_prob = 0.0
        else:
            win_prob = win_against_opponent(new_hand, target, rng, simulations)
        total_prob += prob * win_prob
    return total_prob

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(hand: list[str], target: int) -> str:
    """
    Decide whether to HIT or STAY.

    Parameters
    ----------
    hand : list[str]
        Current cards we hold.
    target : int
        The target score for the whole game.

    Returns
    -------
    str
        "HIT" or "STAY"
    """
    # Fast path: if we have already reached the target we should stay
    if hand_value(hand, target) >= target:
        return "STAY"

    rng = random.Random()          # local RNG, no side‑effects
    stay_win = win_against_opponent(hand, target, rng, simulations=300)
    hit_win = expected_win_after_hit(hand, target, rng, simulations=300)

    # Prefer HIT only if it strictly improves the win chance
    return "HIT" if hit_win > stay_win else "STAY"
