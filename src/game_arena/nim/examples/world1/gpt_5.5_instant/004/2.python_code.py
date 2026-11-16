
def policy(piles: list[int]) -> str:
    """
    Optimal policy for 4-pile misere Nim:
    - Players remove at least one object from one pile.
    - Player who takes the last object loses.

    Returns:
        A legal move string "pile,take".
    """
    n = len(piles)

    # Legal fallback: if any pile is non-empty, take 1 from it.
    # This also handles unexpected inputs defensively.
    fallback_idx = None
    for i, p in enumerate(piles):
        if p > 0:
            fallback_idx = i
            break

    # No legal move exists if all piles are zero. The API should not ask for a move
    # in a terminal state, but return a syntactically valid string as a last resort.
    if fallback_idx is None:
        return "0,1"

    nonzero = [(i, p) for i, p in enumerate(piles) if p > 0]
    big = [(i, p) for i, p in nonzero if p > 1]
    ones_count = sum(1 for p in piles if p == 1)

    # Misere Nim special case: all remaining piles are size 1.
    # If there are k singletons, removing one leaves k-1.
    # In misere play, positions with odd k are winning for the player to move;
    # positions with even k are losing. There is only one kind of legal move here.
    if not big:
        return f"{nonzero[0][0]},1"

    # Misere Nim transition case: exactly one pile larger than 1.
    # We can move directly into the all-ones endgame.
    # Leave an odd number of 1-piles to the opponent, which is losing for them
    # in the all-ones-only misere subgame.
    if len(big) == 1:
        idx, size = big[0]

        # After reducing/removing this big pile:
        # - If ones_count is even, leave one extra singleton: take size - 1.
        # - If ones_count is odd, remove the big pile entirely: take size.
        if ones_count % 2 == 0:
            take = size - 1
        else:
            take = size

        if 1 <= take <= size:
            return f"{idx},{take}"

        # Defensive fallback
        return f"{fallback_idx},1"

    # Normal Nim strategy applies while at least two piles are larger than 1.
    xor_sum = 0
    for p in piles:
        xor_sum ^= p

    # If xor is nonzero, move to xor zero.
    if xor_sum != 0:
        for i, p in enumerate(piles):
            target = p ^ xor_sum
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # If already in a losing xor-zero position, choose a safe legal move.
    # Prefer taking 1 from a largest pile to avoid unnecessarily entering
    # a bad all-ones state sooner.
    max_idx = fallback_idx
    max_val = piles[fallback_idx]
    for i, p in enumerate(piles):
        if p > max_val:
            max_idx = i
            max_val = p

    return f"{max_idx},1"
