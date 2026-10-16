
import functools

# Card order and mapping
CARDS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
CARD_INDEX = {c: i for i, c in enumerate(CARDS)}

# Values for non-ace cards (ace handled separately)
VALUES = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]

FULL_MASK = (1 << 13) - 1

# Precompute base sums (ignoring ace) and ace presence for all masks
BASE_SUM = [0] * (1 << 13)
HAS_ACE = [False] * (1 << 13)
for mask in range(1, 1 << 13):
    lsb = mask & -mask
    idx = lsb.bit_length() - 1
    prev = mask ^ lsb
    BASE_SUM[mask] = BASE_SUM[prev] + (0 if idx == 0 else VALUES[idx])
    HAS_ACE[mask] = HAS_ACE[prev] or (idx == 0)

def total_value(mask: int, target: int) -> int:
    """Compute best hand value <= target using ace as 11 or 1."""
    total = BASE_SUM[mask]
    if HAS_ACE[mask]:
        total += 11
        if total > target:
            total = BASE_SUM[mask] + 1
    return total

@functools.lru_cache(maxsize=None)
def expected_value(mask: int, target: int) -> float:
    """Optimal expected final value from this mask."""
    total = total_value(mask, target)
    if total > target:
        return 0.0  # bust
    stay = float(total)
    remaining = FULL_MASK ^ mask
    if remaining == 0:
        return stay
    # Expected value if hit
    sum_ev = 0.0
    count = 0
    m = remaining
    while m:
        bit = m & -m
        m -= bit
        sum_ev += expected_value(mask | bit, target)
        count += 1
    hit_ev = sum_ev / count
    return stay if stay >= hit_ev else hit_ev

def policy(hand: list[str], target: int) -> str:
    # Convert hand to mask
    mask = 0
    for c in hand:
        idx = CARD_INDEX.get(c)
        if idx is not None:
            mask |= 1 << idx

    total = total_value(mask, target)
    if total > target:
        return "STAY"

    stay = float(total)
    remaining = FULL_MASK ^ mask
    if remaining == 0:
        return "STAY"

    # Compute expected value of hitting
    sum_ev = 0.0
    count = 0
    m = remaining
    while m:
        bit = m & -m
        m -= bit
        sum_ev += expected_value(mask | bit, target)
        count += 1
    hit_ev = sum_ev / count

    return "HIT" if hit_ev > stay else "STAY"
