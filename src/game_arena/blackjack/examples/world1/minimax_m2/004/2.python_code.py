
import sys
import threading
from functools import lru_cache
from typing import List, Dict, Tuple

# Card definitions
CARD_ORDER = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_TO_BIT = {c: i for i, c in enumerate(CARD_ORDER)}
FULL_MASK = (1 << 13) - 1

# Card values (Ace as 11 for now, will adjust later)
CARD_VALUE = {
    "A": 11,
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}

# Precompute bitlist for each mask
BITLIST = [[] for _ in range(1 << 13)]
for mask in range(1 << 13):
    bits = []
    m = mask
    while m:
        # get lowest set bit index
        lsb = m & -m
        i = (lsb.bit_length() - 1)
        bits.append(i)
        m ^= lsb
    BITLIST[mask] = bits

# Precompute sum_non_ace and ace_present for each mask
SUM_NON_ACE = [0] * (1 << 13)
ACE_PRESENT = [False] * (1 << 13)
for mask in range(1 << 13):
    s = 0
    has_ace = False
    for i in range(13):
        if mask & (1 << i):
            rank = CARD_ORDER[i]
            if rank == "A":
                has_ace = True
            else:
                s += CARD_VALUE[rank]
    SUM_NON_ACE[mask] = s
    ACE_PRESENT[mask] = has_ace

def compute_hand_sum(mask: int, target: int) -> int:
    """Return the value of the hand represented by mask (cards in hand) given target T.
    Ace counts as 11 unless it would make the hand exceed target, then it counts as 1.
    """
    total = SUM_NON_ACE[mask] + (11 if ACE_PRESENT[mask] else 0)
    if ACE_PRESENT[mask] and total > target:
        total -= 10
    return total

# Global caches for opponent distribution and our DP per target
OPPOSITE_DIST_CACHE: Dict[int, Tuple[float, List[float]]] = {}
DP_CACHE: Dict[int, List[str]] = {}  # mask -> action for each target
DP_VALUES_CACHE: Dict[int, List[float]] = {}  # mask -> expected win probability for each target

# Opponent policy: hit until sum >= DEALER_THRESHOLD (stand on 17)
DEALER_THRESHOLD = 17

def opponent_distribution(target: int) -> Tuple[float, List[float]]:
    """Compute opponent's bust probability and sum distribution when they hit until sum >= 17.
    Returns (bust_prob, sum_prob_list) where sum_prob_list[s] is probability opponent ends with sum s (0 <= s <= target).
    For target < 17, opponent busts for sure.
    """
    if target < DEALER_THRESHOLD:
        # Opponent busts with probability 1
        return 1.0, [0.0] * (target + 1)
    if target in OPPOSITE_DIST_CACHE:
        return OPPOSITE_DIST_CACHE[target]

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def opp_dist(mask_rem: int) -> Tuple[float, List[float]]:
        # hand is complement of mask_rem
        hand_mask = FULL_MASK ^ mask_rem
        hand_sum = compute_hand_sum(hand_mask, target)
        # Bust case
        if hand_sum > target:
            bust_prob = 1.0
            sum_prob = [0.0] * (target + 1)
            return bust_prob, sum_prob
        # Stop if hand sum >= 17 (dealer stands)
        if hand_sum >= DEALER_THRESHOLD:
            bust_prob = 0.0
            sum_prob = [0.0] * (target + 1)
            if hand_sum <= target:
                sum_prob[hand_sum] = 1.0
            else:
                # hand_sum > target but this case is already handled above
                pass
            return bust_prob, sum_prob
        # No cards left, cannot draw further
        if mask_rem == 0:
            bust_prob = 0.0
            sum_prob = [0.0] * (target + 1)
            if hand_sum <= target:
                sum_prob[hand_sum] = 1.0
            else:
                # should not happen because hand_sum > target already handled
                pass
            return bust_prob, sum_prob
        # Otherwise, need to draw a card
        bits = BITLIST[mask_rem]
        n = len(bits)
        bust_acc = 0.0
        sum_acc = [0.0] * (target + 1)
        for i in bits:
            new_mask = mask_rem ^ (1 << i)
            b_i, p_i = opp_dist(new_mask)
            bust_acc += b_i / n
            # accumulate sum probabilities
            for s in range(target + 1):
                sum_acc[s] += p_i[s] / n
        return bust_acc, sum_acc

    bust_prob, sum_prob = opp_dist(FULL_MASK)
    OPPOSITE_DIST_CACHE[target] = (bust_prob, sum_prob)
    return bust_prob, sum_prob

def win_prob_given_sum(s: int, target: int, bust_prob: float, sum_prob: List[float]) -> float:
    """Probability of winning if we finish with sum s (assuming opponent distribution is known)."""
    # opponent bust probability
    p_bust = bust_prob
    # probability opponent sum < s
    prob_less = sum(sum_prob[:s]) if s > 0 else 0.0
    prob_equal = sum_prob[s] if s <= target else 0.0
    # If opponent busts, we win; otherwise compare sums
    win_prob = p_bust + (1.0 - p_bust) * (prob_less + 0.5 * prob_equal)
    return win_prob

def compute_policy_for_target(target: int) -> List[str]:
    """Compute optimal actions for all masks for a given target using DP.
    Returns a list actions where actions[mask] is 'HIT' or 'STAY'.
    """
    if target in DP_CACHE:
        return DP_CACHE[target]
    # Get opponent distribution
    bust_prob, sum_prob = opponent_distribution(target)

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dp(mask_rem: int) -> float:
        hand_mask = FULL_MASK ^ mask_rem
        hand_sum = compute_hand_sum(hand_mask, target)
        # Bust case
        if hand_sum > target:
            return 0.0
        # If hand_sum >= target, we must stay (hand_sum == target)
        if hand_sum >= target:
            return win_prob_given_sum(hand_sum, target, bust_prob, sum_prob)
        # Otherwise hand_sum < target
        stay_val = win_prob_given_sum(hand_sum, target, bust_prob, sum_prob)
        # Compute hit value
        bits = BITLIST[mask_rem]
        n = len(bits)
        hit_val = 0.0
        for i in bits:
            new_mask = mask_rem ^ (1 << i)
            val = dp(new_mask)
            hit_val += val
        hit_val /= n
        # Choose best
        return max(stay_val, hit_val)

    # Compute actions for all masks
    actions = ["STAY"] * (1 << 13)
    for mask_rem in range(1 << 13):
        hand_mask = FULL_MASK ^ mask_rem
        hand_sum = compute_hand_sum(hand_mask, target)
        if hand_sum > target:
            actions[mask_rem] = "STAY"  # already bust, but shouldn't happen
            continue
        if hand_sum >= target:
            actions[mask_rem] = "STAY"
            continue
        stay_val = win_prob_given_sum(hand_sum, target, bust_prob, sum_prob)
        bits = BITLIST[mask_rem]
        n = len(bits)
        hit_val = 0.0
        for i in bits:
            new_mask = mask_rem ^ (1 << i)
            val = dp(new_mask)
            hit_val += val
        hit_val /= n
        actions[mask_rem] = "HIT" if hit_val > stay_val else "STAY"
    DP_CACHE[target] = actions
    return actions

# Precompute policies for all targets 10..30 lazily when first needed
for T in range(10, 31):
    compute_policy_for_target(T)

def policy(hand: List[str], target: int) -> str:
    """Return 'HIT' or 'STAY' based on the current hand and target.
    hand: list of card ranks currently held by the player.
    target: the target score for the game.
    """
    # Build mask of cards in hand
    mask_hand = 0
    for card in hand:
        if card in CARD_TO_BIT:
            mask_hand |= (1 << CARD_TO_BIT[card])
        else:
            # Invalid card, ignore (should not happen)
            pass
    mask_rem = FULL_MASK ^ mask_hand
    actions = compute_policy_for_target(target)
    return actions[mask_rem]
