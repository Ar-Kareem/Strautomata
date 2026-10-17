
import itertools
from typing import List, Tuple

BoardSize = 19

def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def policy(me: List[Tuple[int, int]],
           opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Return a legal Go move for a 19×19 board.

    Arguments:
        me:      list of (row, col) coordinates of our stones.
        opponent:list of (row, col) coordinates of opponent stones.

    Returns:
        (row, col) of the chosen move, or (0, 0) to pass.
    """
    occupied = set(me) | set(opponent)

    # Opening move – board empty
    if not me and not opponent:
        centre = (10, 10)
        if centre not in occupied:
            return centre
        # fallback: first empty point
        for r in range(1, BoardSize + 1):
            for c in range(1, BoardSize + 1):
                if (r, c) not in occupied:
                    return (r, c)

    best_move = None
    best_score = -float('inf')

    # Pre‑compute distances to own and opponent stones for each empty point
    for r in range(1, BoardSize + 1):
        for c in range(1, BoardSize + 1):
            pt = (r, c)
            if pt in occupied:
                continue

            # distance to nearest opponent stone
            if opponent:
                d_opp = min(manhattan(pt, opp) for opp in opponent)
            else:
                d_opp = BoardSize * 2  # maximal possible distance

            # distance to nearest own stone
            if me:
                d_me = min(manhattan(pt, own) for own in me)
            else:
                d_me = 0  # no own stones, treat as zero distance

            # higher score = far from opponent & close to our own stones
            score = d_opp - d_me

            if score > best_score:
                best_score = score
                best_move = pt

    # If for any reason we didn't find a move (board full), pass.
    if best_move is None:
        return (0, 0)

    return best_move
