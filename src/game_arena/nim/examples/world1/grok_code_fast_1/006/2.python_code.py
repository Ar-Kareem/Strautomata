
import functools

@functools.lru_cache(maxsize=None)
def is_losing(piles_tuple: tuple[int, ...]) -> bool:
    piles = list(piles_tuple)
    if all(p == 0 for p in piles):
        return True
    for pile in range(4):
        for take in range(1, piles[pile] + 1):
            new_piles = piles[:]
            new_piles[pile] -= take
            new_tuple = tuple(new_piles)
            if is_losing(new_tuple):
                return False
    return True

def policy(piles: list[int]) -> str:
    for pile in range(4):
        for take in range(1, piles[pile] + 1):
            new_piles = piles[:]
            new_piles[pile] -= take
            if not all(p == 0 for p in new_piles) and is_losing(tuple(new_piles)):
                return f"{pile},{take}"
    # No winning move, pick a default legal move
    for pile in range(4):
        if piles[pile] > 0:
            return f"{pile},1"
    # Should not reach here if game is ongoing, but safe fallback
    raise ValueError("No legal moves available")
