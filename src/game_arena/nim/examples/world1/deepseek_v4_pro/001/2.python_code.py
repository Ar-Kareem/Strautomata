
def policy(piles: list[int]) -> str:
    """
    Returns the optimal move in misère Nim (4 piles).
    Format: 'pile,take' (0-based pile index, number to remove).
    """
    n = len(piles)
    # compute nim-sum (XOR of all piles)
    x = 0
    for p in piles:
        x ^= p

    # Case 1: all piles are 0 or 1 (trivial endgame)
    if all(p <= 1 for p in piles):
        for i, p in enumerate(piles):
            if p >= 1:
                return f"{i},1"
        # Fallback (should not be reached in a live game)
        return "0,1"

    # Case 2: at least one pile > 1
    if x != 0:
        # Winning position: find a move that makes nim-sum zero
        for i, p in enumerate(piles):
            if (p ^ x) < p:
                take = p - (p ^ x)
                # Check if this move leaves all piles <= 1
                new_piles = piles.copy()
                new_piles[i] -= take
                if all(np <= 1 for np in new_piles):
                    # Misère exception: leave an odd number of 1s
                    target = 1 - (p ^ x)
                    take = p - target
                return f"{i},{take}"
    else:
        # x == 0, losing position: take 1 from the first pile > 1
        for i, p in enumerate(piles):
            if p > 1:
                return f"{i},1"
        # Fallback: take 1 from any pile (only reaches if all <=1, handled above)
        for i, p in enumerate(piles):
            if p > 0:
                return f"{i},1"
        return "0,1"
