
"""Misere Nim (4 piles) - optimal policy.

The player who takes the last object loses (misere rule).
Strategy (classical misere Nim theory):
  1. If at most one pile has more than one object, leave the opponent
     an odd number of 1-object piles.
  2. Otherwise play normal Nim: move to a position with nim-sum (XOR) 0.
  3. If the nim-sum is already 0 the position is theoretically losing;
     take 1 from the largest pile to prolong the game.
"""


def policy(piles: list[int]) -> str:
    n = len(piles)
    big = [i for i in range(n) if piles[i] > 1]
    ones = [i for i in range(n) if piles[i] == 1]

    # Case A: every pile has 0 or 1 objects.
    if len(big) == 0:
        if ones:
            # Taking one object flips the parity of 1-piles (ideal if we
            # can leave an odd count; forced move otherwise).
            return f"{ones[0]},1"
        # Terminal position (no legal move exists); should never occur.
        return "0,1"

    # Case B: exactly one pile larger than 1 (misere endgame exception).
    if len(big) == 1:
        i = big[0]
        k = len(ones)
        # Leave an odd number of 1-object piles for the opponent.
        target = 0 if (k % 2 == 1) else 1
        take = piles[i] - target
        if take < 1:
            take = 1  # safety; cannot happen since piles[i] > 1
        return f"{i},{take}"

    # Case C: two or more piles larger than 1 -> normal Nim strategy.
    s = 0
    for p in piles:
        s ^= p

    if s != 0:
        for i in range(n):
            t = piles[i] ^ s
            if t < piles[i]:
                return f"{i},{piles[i] - t}"

    # Nim-sum is 0: losing under perfect play. Take 1 from the largest
    # pile to keep the game going and maximize opponent error chances.
    best = 0
    for i in range(1, n):
        if piles[i] > piles[best]:
            best = i
    if piles[best] == 0:
        return "0,1"  # safety fallback; should never occur
    return f"{best},1"
