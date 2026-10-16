
from functools import lru_cache

@lru_cache(maxsize=None)
def is_losing_state(piles_tuple):
    piles = list(piles_tuple)
    total = sum(piles)
    if total == 0:
        return False  # Though this shouldn't be reached
    has_good_move = False
    for i in range(4):
        if piles[i] >= 1:
            for take in range(1, piles[i] + 1):
                new_piles = piles[:]
                new_piles[i] -= take
                new_total = sum(new_piles)
                if new_total == 0:
                    continue  # Skip moves that leave all piles zero
                if not is_losing_state(tuple(new_piles)):
                    has_good_move = True
    return not has_good_move

def policy(piles):
    # If losing position, just pick any legal move
    if is_losing_state(tuple(piles)):
        for i in range(4):
            if piles[i] >= 1:
                return f"{i},{1}"
    # Otherwise, pick a move that leads to a losing position for the opponent
    else:
        for i in range(4):
            if piles[i] >= 1:
                for take in range(1, piles[i] + 1):
                    new_piles = piles[:]
                    new_piles[i] -= take
                    if sum(new_piles) > 0 and not is_losing_state(tuple(new_piles)):
                        return f"{i},{take}"
    # Fallback (should not reach if logic is correct)
    for i in range(4):
        if piles[i] >= 1:
            return f"{i},{1}"
    return "0,1"  # Extremely unlikely fallback
