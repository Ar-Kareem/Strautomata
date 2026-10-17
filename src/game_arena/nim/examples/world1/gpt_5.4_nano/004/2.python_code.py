
from functools import reduce
from operator import ixor

def policy(piles: list[int]) -> str:
    # Ensure valid length
    if len(piles) != 4:
        raise ValueError("Expected 4 piles")

    nonempty = [i for i, v in enumerate(piles) if v > 0]
    if not nonempty:
        # No legal move exists in this state; but game should have ended.
        # Return a legal-looking placeholder (won't be used).
        return "0,1"

    # Misère Nim special handling:
    # If every non-empty pile has size 1, then the player should take exactly enough
    # from one pile to leave an even number of non-empty piles.
    if all(piles[i] == 1 for i in nonempty):
        # Each move must take 1 from some pile.
        # If there are k non-empty piles, current player loses iff k is odd
        # (because taking 1 reduces to k-1; the player who faces 1 non-empty loses).
        # Therefore, to win: when k is odd, make move to leave even -> take from any pile.
        k = len(nonempty)
        # If k is odd => winning move (leave k-1 even) by taking 1 from any non-empty pile.
        # If k is even => losing position; still must return a legal move: take 1 from any pile.
        pile = nonempty[0]
        return f"{pile},1"

    # General case: compute XOR and use normal Nim move to make XOR = 0.
    x = 0
    for v in piles:
        x ^= v

    # If XOR is already 0, position is losing under optimal play.
    # Still must make a legal move: remove 1 from the first non-empty pile.
    if x == 0:
        pile = nonempty[0]
        return f"{pile},1"

    # Otherwise, find a pile to reduce so that new XOR becomes 0.
    for i in nonempty:
        vi = piles[i]
        target = vi ^ x  # desired new size for this pile
        if target < vi:
            take = vi - target
            if 1 <= take <= vi:
                return f"{i},{take}"

    # Fallback (should not happen): remove 1 from first non-empty pile.
    pile = nonempty[0]
    return f"{pile},1"
