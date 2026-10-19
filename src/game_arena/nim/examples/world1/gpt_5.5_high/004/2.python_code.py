
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Last player to take an object loses.
    - Return format: "pile,take".
    """

    # Basic legal fallback. The all-zero state should never be given to a player
    # to move, because the game is already over.
    def first_legal() -> str:
        for i, h in enumerate(piles):
            if h > 0:
                return f"{i},1"
        return "0,0"

    ones = sum(1 for h in piles if h == 1)
    big_indices = [i for i, h in enumerate(piles) if h > 1]

    # Case 1: only piles of size 0 or 1 remain.
    # With k singletons, positions with odd k are losing, even k are winning.
    # In either case, the only kind of legal move is to take one singleton.
    if not big_indices:
        return first_legal()

    # Case 2: exactly one pile is larger than 1.
    # Choose whether to leave that pile as 0 or 1 so that the opponent faces
    # an odd number of singleton piles, which is losing in misere Nim.
    if len(big_indices) == 1:
        i = big_indices[0]
        h = piles[i]

        # If current singleton count is odd, remove the large pile completely.
        # If it is even, leave one object in the large pile.
        target = 0 if (ones % 2 == 1) else 1
        take = h - target

        if take >= 1:
            return f"{i},{take}"
        return first_legal()

    # Case 3: at least two piles are larger than 1.
    # Misere Nim is the same as normal Nim here: move to xor-sum 0 when possible.
    xor_sum = 0
    for h in piles:
        xor_sum ^= h

    if xor_sum != 0:
        for i, h in enumerate(piles):
            target = h ^ xor_sum
            if target < h:
                take = h - target
                if take >= 1:
                    return f"{i},{take}"

    # If xor_sum is already 0, this is a losing position against perfect play.
    # No move can force a win, so return a legal move.  When there are exactly
    # two large piles, removing one of them creates a common misere-Nim trap
    # for non-perfect opponents.
    if len(big_indices) == 2:
        i = max(big_indices, key=lambda idx: piles[idx])
        return f"{i},{piles[i]}"

    # Otherwise, make a safe legal move from the largest pile.
    i = max((idx for idx, h in enumerate(piles) if h > 0), key=lambda idx: piles[idx])
    return f"{i},1"
