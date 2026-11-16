
def _is_losing_for_mover(p):
    """True if the player to move from position p loses under misère Nim (optimal play)."""
    if max(p) <= 1:
        ones = sum(1 for x in p if x == 1)
        return ones % 2 == 1
    x = 0
    for v in p:
        x ^= v
    return x == 0


def policy(piles: list[int]) -> str:
    piles = list(piles)
    n = len(piles)

    # Enumerate all legal moves; pick one that leaves opponent in a losing position.
    winning_moves = []
    legal_moves = []
    for i in range(n):
        for take in range(1, piles[i] + 1):
            new_p = piles[:]
            new_p[i] -= take
            legal_moves.append((i, take))
            if _is_losing_for_mover(new_p):
                winning_moves.append((i, take))

    if winning_moves:
        # Prefer moves that keep the game long-ish (avoid giving unnecessary info),
        # but any winning move is theoretically sufficient. Pick the first.
        i, take = winning_moves[0]
        return f"{i},{take}"

    if legal_moves:
        # Losing position: stall by taking 1 from the largest pile to prolong game
        # and give the opponent chances to err.
        largest = max(range(n), key=lambda k: piles[k])
        if piles[largest] >= 1:
            return f"{largest},1"
        i, take = legal_moves[0]
        return f"{i},{take}"

    # No legal moves (all piles empty) - should not happen; return something.
    return "0,1"
