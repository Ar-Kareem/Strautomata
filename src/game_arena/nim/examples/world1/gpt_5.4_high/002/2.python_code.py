
def _first_legal_move(piles: list[int]) -> str:
    for i, p in enumerate(piles):
        if p > 0:
            return f"{i},1"
    # Terminal position should not be queried; no legal move exists.
    return "0,1"


def _trappy_losing_move(piles: list[int]) -> str:
    """
    In a theoretical losing position, no move can force a win.
    This heuristic prefers moves that leave the opponent with exactly
    one heap > 1, which often traps policies that incorrectly play
    normal Nim in the misère endgame.
    """
    total = sum(piles)
    best_move = None
    best_score = None

    for i, p in enumerate(piles):
        if p <= 1:
            continue

        # Only consider strategically meaningful targets: 1 or 0.
        for target in (1, 0):
            if target >= p:
                continue
            if target == 0 and total == p:
                continue  # would take the last object and lose immediately

            new_piles = piles[:]
            new_piles[i] = target

            ones = sum(1 for x in new_piles if x == 1)
            big = sum(1 for x in new_piles if x > 1)
            largest_big = max((x for x in new_piles if x > 1), default=0)

            # Prefer:
            # 1) exactly one big heap
            # 2) in that case, an even number of ones (less obvious winning reply)
            # 3) fewer big heaps
            # 4) a larger remaining big heap
            # 5) more remaining stones
            score = (
                1 if big == 1 else 0,
                1 if (big == 1 and ones % 2 == 0) else 0,
                -big,
                largest_big,
                sum(new_piles),
            )

            if best_score is None or score > best_score:
                best_score = score
                best_move = (i, p - target)

    if best_move is not None:
        return f"{best_move[0]},{best_move[1]}"

    return _first_legal_move(piles)


def policy(piles: list[int]) -> str:
    # Safe fallback if ever called on terminal input.
    if not any(p > 0 for p in piles):
        return "0,1"

    ones = sum(1 for p in piles if p == 1)
    big_indices = [i for i, p in enumerate(piles) if p > 1]
    big_count = len(big_indices)

    # Nim-sum
    x = 0
    for p in piles:
        x ^= p

    # Case 1: all nonzero heaps are 1s
    # Winning iff the count of ones is even; in either case the only sensible move is to take one 1.
    if big_count == 0:
        return _first_legal_move(piles)

    # Case 2: exactly one heap > 1
    # Leave an odd number of 1-heaps to the opponent.
    if big_count == 1:
        i = big_indices[0]
        if ones % 2 == 0:
            take = piles[i] - 1  # reduce big heap to 1
        else:
            take = piles[i]      # remove big heap entirely

        if 1 <= take <= piles[i]:
            return f"{i},{take}"
        return _first_legal_move(piles)

    # Case 3: at least two heaps > 1
    # Normal Nim rule applies: make xor zero.
    if x != 0:
        for i, p in enumerate(piles):
            target = p ^ x
            if target < p:
                take = p - target
                if 1 <= take <= p:
                    return f"{i},{take}"

    # Theoretical losing position: return a legal move, preferring trap-prone states.
    return _trappy_losing_move(piles)
