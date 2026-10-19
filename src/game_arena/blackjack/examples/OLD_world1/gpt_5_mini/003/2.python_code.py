
from functools import lru_cache

# Ranks and their indices for bitmasking
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_TO_INDEX = {r: i for i, r in enumerate(RANKS)}

# Non-Ace card values
NON_ACE_VALUE = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10
}


def policy(hand: list[str], target: int) -> str:
    """
    Decide whether to "HIT" or "STAY" given the current hand and target.
    The policy maximizes the expected final hand total (<= target) assuming
    uniform random draws from the remaining cards in our 13-card deck.
    """

    # Compute initial sum excluding any Ace, and whether we have an Ace
    sum_no_ace = 0
    ace_flag = False
    for c in hand:
        if c == "A":
            ace_flag = True
        else:
            sum_no_ace += NON_ACE_VALUE.get(c, 0)

    # Build remaining-card mask: bit i = 1 means the rank RANKS[i] is available to draw
    full_mask = (1 << len(RANKS)) - 1
    mask = full_mask
    for c in hand:
        # remove the card from remaining deck if present
        idx = RANK_TO_INDEX.get(c)
        if idx is not None:
            mask &= ~(1 << idx)

    # Helper to compute effective total given sum_no_ace and ace_flag
    def effective_total(sum_no_ace: int, ace_flag: bool) -> int:
        if ace_flag:
            if sum_no_ace + 11 <= target:
                return sum_no_ace + 11
            else:
                return sum_no_ace + 1
        else:
            return sum_no_ace

    # Memoized recursion: expected best final total (<= target) achievable from state
    @lru_cache(maxsize=None)
    def expected_best(sum_no_ace: int, ace_flag_int: int, mask_int: int) -> float:
        ace_flag = bool(ace_flag_int)
        total = effective_total(sum_no_ace, ace_flag)
        # If already busted, value 0 (cannot improve)
        if total > target:
            return 0.0

        # Value if we STAY now: our final total (we assume larger final total is better)
        stay_value = float(total)

        # If no cards left, must stay
        if mask_int == 0:
            return stay_value

        # Value if we HIT: expected value over next-card uniform draw, then play optimally
        # For each available rank bit in mask, simulate drawing it
        hits = []
        m = mask_int
        # iterate bits
        idx = 0
        while m:
            if m & 1:
                rank = RANKS[idx]
                next_mask = mask_int & ~(1 << idx)
                if rank == "A":
                    # drawing Ace: set ace_flag (only one Ace exists)
                    next_sum_no_ace = sum_no_ace
                    next_ace_flag = True
                else:
                    next_sum_no_ace = sum_no_ace + NON_ACE_VALUE[rank]
                    next_ace_flag = ace_flag  # unchanged

                # After drawing, compute child's expected best recursively
                child_val = expected_best(next_sum_no_ace, int(next_ace_flag), next_mask)
                hits.append(child_val)
            m >>= 1
            idx += 1

        if not hits:
            # No available hits; must stay
            return stay_value

        hit_value = sum(hits) / len(hits)
        # Return the best of staying now vs hitting (and playing optimally thereafter)
        return max(stay_value, hit_value)

    # If currently bust, no reason to hit
    current_total = effective_total(sum_no_ace, ace_flag)
    if current_total > target:
        return "STAY"

    # Compute stay and hit expected values for decision at this moment
    stay_value = float(current_total)

    # If no cards left -> must stay
    if mask == 0:
        return "STAY"

    # Compute expected value of hitting once and then playing optimally
    hits_values = []
    m = mask
    idx = 0
    while m:
        if m & 1:
            rank = RANKS[idx]
            next_mask = mask & ~(1 << idx)
            if rank == "A":
                next_sum_no_ace = sum_no_ace
                next_ace_flag = True
            else:
                next_sum_no_ace = sum_no_ace + NON_ACE_VALUE[rank]
                next_ace_flag = ace_flag
            child_val = expected_best(next_sum_no_ace, int(next_ace_flag), next_mask)
            hits_values.append(child_val)
        m >>= 1
        idx += 1

    if not hits_values:
        return "STAY"

    hit_value = sum(hits_values) / len(hits_values)

    # Choose HIT if expected value from hitting (and playing optimally afterwards)
    # strictly improves over staying. Tie-break to STAY.
    if hit_value > stay_value + 1e-9:
        return "HIT"
    else:
        return "STAY"
