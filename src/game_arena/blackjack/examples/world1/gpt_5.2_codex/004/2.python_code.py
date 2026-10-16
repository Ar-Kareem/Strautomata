
from functools import lru_cache

# Card ranks in fixed order
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
INDEX = {r: i for i, r in enumerate(RANKS)}

# Precompute non-ace values for each card
NON_ACE_VALUE = []
for r in RANKS:
    if r == "A":
        NON_ACE_VALUE.append(0)
    elif r in ("J", "Q", "K"):
        NON_ACE_VALUE.append(10)
    else:
        NON_ACE_VALUE.append(int(r))

NUM_CARDS = 13
FULL_MASK = (1 << NUM_CARDS) - 1

# Precompute sum of non-ace values and ace presence for all masks
SUM_NONACE = [0] * (1 << NUM_CARDS)
HAS_ACE = [False] * (1 << NUM_CARDS)

for mask in range(1 << NUM_CARDS):
    s = 0
    ace = False
    for i in range(NUM_CARDS):
        if mask & (1 << i):
            if RANKS[i] == "A":
                ace = True
            else:
                s += NON_ACE_VALUE[i]
    SUM_NONACE[mask] = s
    HAS_ACE[mask] = ace

def hand_value(mask: int, target: int) -> int:
    """Compute hand value with ace as 11 or 1."""
    s = SUM_NONACE[mask]
    if HAS_ACE[mask]:
        if s + 11 <= target:
            return s + 11
        else:
            return s + 1
    else:
        return s

@lru_cache(maxsize=None)
def best_value(mask: int, target: int) -> float:
    """
    Expected optimal final score from this hand state.
    Busts yield 0. Assumes optimal play henceforth.
    """
    total = hand_value(mask, target)
    if total > target:
        return 0.0  # already bust

    stay_val = float(total)

    if mask == FULL_MASK:
        return stay_val  # no cards left

    # Expected value if we hit now and then play optimally
    rem = [i for i in range(NUM_CARDS) if not (mask & (1 << i))]
    hit_val = 0.0
    for i in rem:
        hit_val += best_value(mask | (1 << i), target)
    hit_val /= len(rem)

    return max(stay_val, hit_val)

def expected_hit_value(mask: int, target: int) -> float:
    """Expected value if we choose HIT now (then play optimally)."""
    if mask == FULL_MASK:
        return -1.0  # cannot hit
    rem = [i for i in range(NUM_CARDS) if not (mask & (1 << i))]
    hit_val = 0.0
    for i in rem:
        hit_val += best_value(mask | (1 << i), target)
    return hit_val / len(rem)

def policy(hand: list[str], target: int) -> str:
    # Build hand mask
    mask = 0
    for card in hand:
        if card in INDEX:
            mask |= (1 << INDEX[card])

    total = hand_value(mask, target)

    # If already bust, must stay
    if total > target:
        return "STAY"

    # If no cards left, must stay
    if mask == FULL_MASK:
        return "STAY"

    stay_val = float(total)
    hit_val = expected_hit_value(mask, target)

    if hit_val > stay_val:
        return "HIT"
    else:
        return "STAY"
