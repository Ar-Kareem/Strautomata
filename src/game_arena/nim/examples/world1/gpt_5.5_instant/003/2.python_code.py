
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Last player to take an object loses.
    - Return format: 'pile,take'
    """
    # Defensive normalization; keep original indices.
    if not piles or len(piles) != 4:
        piles = list(piles)[:4] + [0] * max(0, 4 - len(piles))

    # Find all legal piles.
    nonzero = [i for i, x in enumerate(piles) if x > 0]
    if not nonzero:
        # No legal move should be requested in a finished game, but return a
        # syntactically valid-looking fallback. Arena should never call here.
        return "0,1"

    ones = [i for i in nonzero if piles[i] == 1]
    big = [i for i in nonzero if piles[i] > 1]

    # Endgame: all nonzero piles have size 1.
    # With k ones and misere play, positions with odd k are winning, even k losing.
    # Legal move is necessarily to take 1 from any nonzero pile.
    if not big:
        return f"{nonzero[0]},1"

    # Compute nim-sum.
    xor_sum = 0
    for x in piles:
        xor_sum ^= x

    # If xor is zero, this is a losing position under perfect play.
    # Still return a robust legal move. Prefer reducing the largest pile by 1,
    # except when that would enter the all-ones phase incorrectly; fallback is legal.
    if xor_sum == 0:
        idx = max(nonzero, key=lambda i: piles[i])
        return f"{idx},1"

    # Try the normal Nim xor move.
    for i, x in enumerate(piles):
        target = x ^ xor_sum
        if target < x:
            take = x - target

            # Misere adjustment: if this move would leave no big piles, choose
            # a move that leaves an odd number of 1-piles to the opponent.
            resulting = piles[:]
            resulting[i] = target
            resulting_big_count = sum(1 for v in resulting if v > 1)

            if resulting_big_count == 0:
                current_ones = sum(1 for v in piles if v == 1)
                # We are reducing one big pile to either 0 or 1.
                # Need final number of ones odd for opponent.
                # If current_ones is even, leave target 1; if odd, leave target 0.
                desired_target = 1 if current_ones % 2 == 0 else 0

                # Choose a big pile that can be reduced to desired_target.
                # Since pile is > 1, taking pile-desired_target is legal.
                j = big[0]
                adjusted_take = piles[j] - desired_target
                return f"{j},{adjusted_take}"

            return f"{i},{take}"

    # Absolute safety fallback: first legal pile, take 1.
    i = nonzero[0]
    return f"{i},1"
