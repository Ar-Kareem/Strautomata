
def policy(piles: list[int]) -> str:
    # Misère Nim optimal play for 4 piles
    # Game rule: taking the last object loses.
    # Return format: 'pile,take'
    nonzero = [x for x in piles if x > 0]

    # If all remaining piles have size 1, best move is to take 1 from a single pile
    # (since any move would otherwise likely force taking the last).
    if nonzero and all(x == 1 for x in nonzero):
        for i, v in enumerate(piles):
            if v == 1:
                return f"{i},1"

    # Otherwise, use normal Nim strategy to make nim-sum zero.
    nim_sum = 0
    for v in piles:
        nim_sum ^= v

    # If nim_sum is already zero, any move loses under optimal play;
    # pick a legal move deterministically.
    if nim_sum == 0:
        for i, v in enumerate(piles):
            if v > 0:
                return f"{i},1"

    # Find a pile to reduce: choose i such that reducing to (piles[i] ^ nim_sum)
    # results in a smaller nonnegative number.
    for i, v in enumerate(piles):
        target = v ^ nim_sum
        if target < v:
            take = v - target
            # take must be legal and >=1
            if 1 <= take <= v:
                return f"{i},{take}"

    # Fallback (should not happen)
    for i, v in enumerate(piles):
        if v > 0:
            return f"{i},1"
    # If no legal moves (game over), return dummy (should never be called)
    return "0,1"
