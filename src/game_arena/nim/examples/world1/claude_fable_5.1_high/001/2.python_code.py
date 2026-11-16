
def _losing_for_mover(piles):
    """Return True if the player to move in this misère Nim position loses under perfect play."""
    if all(p <= 1 for p in piles):
        ones = sum(1 for p in piles if p == 1)
        return ones % 2 == 1
    x = 0
    for p in piles:
        x ^= p
    return x == 0


def policy(piles: list[int]) -> str:
    piles = [int(p) for p in piles]
    n = len(piles)

    # Look for a winning move: one that leaves the opponent in a losing position.
    for i in range(n):
        for take in range(1, piles[i] + 1):
            new_piles = piles[:]
            new_piles[i] -= take
            if _losing_for_mover(new_piles):
                return f"{i},{take}"

    # No winning move (we are in a losing position). Stall: take 1 from the largest pile.
    best_i = -1
    best_v = 0
    for i in range(n):
        if piles[i] > best_v:
            best_v = piles[i]
            best_i = i
    if best_i >= 0:
        return f"{best_i},1"

    # Fallback (should not happen if the game is not over): any legal move.
    for i in range(n):
        if piles[i] > 0:
            return f"{i},1"
    return "0,1"
