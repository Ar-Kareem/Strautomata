
import sys

cache = {}

def is_winning(piles):
    piles = tuple(piles)
    if piles in cache:
        return cache[piles]
    possible_win = False
    for i in range(4):
        for t in range(1, piles[i] + 1):
            new_p = list(piles)
            new_p[i] -= t
            if all(x == 0 for x in new_p):
                continue  # Moving to all zero is a loss, so skip
            if not is_winning(new_p):
                possible_win = True
                break
    cache[piles] = possible_win
    return possible_win

def policy(piles: list[int]) -> str:
    piles_tuple = tuple(piles)
    if is_winning(piles_tuple):
        # Find a move to a losing position for the opponent
        for i in range(4):
            for t in range(1, piles[i] + 1):
                new_p = list(piles)
                new_p[i] -= t
                if all(x == 0 for x in new_p):
                    continue
                if not is_winning(tuple(new_p)):
                    return f"{i},{t}"
    else:
        # Losing position: Make a legal move, e.g., take all from the first pile with objects
        for i in range(4):
            if piles[i] > 0:
                return f"{i},{piles[i]}"
    # Should not reach here if piles are valid, but as a fallback (though not necessary)
    return "0,1"  # Arbitrary legal move assuming pile 0 has at least 1
