
import random
from typing import List, Tuple, Dict

Point = Tuple[int, int]

def _is_legal(move: Point, occupied: set) -> bool:
    """Return True if move is on the board and not occupied."""
    r, c = move
    return 1 <= r <= 19 and 1 <= c <= 19 and move not in occupied

def _has_empty_neighbour(move: Point, occupied: set) -> bool:
    """A very cheap suicide guard: a move is illegal only if all orthogonal
    neighbours are occupied by the opponent (or board edge). We accept the move
    if at least one neighbour is empty."""
    r, c = move
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19:
            if (nr, nc) not in occupied:
                return True
    return False  # every neighbour is occupied (or off‑board)

def policy(me: List[Point],
           opponent: List[Point],
           memory: Dict) -> Tuple[Point, Dict]:
    """
    Return the next move for the player.
    me          – list of my stones (row, col)
    opponent    – list of opponent stones (row, col)
    memory      – persistent dict (unused here)
    """
    occupied = set(me) | set(opponent)

    # 1. Candidates adjacent to my own stones
    adj_candidates = []
    for r, c in me:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            cand = (nr, nc)
            if _is_legal(cand, occupied) and _has_empty_neighbour(cand, occupied):
                adj_candidates.append(cand)

    if adj_candidates:
        # choose the first (could random.choice for more variety)
        move = adj_candidates[0]
        return move, memory

    # 2. Centre point if free
    centre = (10, 10)
    if _is_legal(centre, occupied):
        return centre, memory

    # 3. Any empty point (deterministic first in row‑major order)
    for r in range(1, 20):
        for c in range(1, 20):
            pt = (r, c)
            if _is_legal(pt, occupied) and _has_empty_neighbour(pt, occupied):
                return pt, memory

    # 4. No legal moves left → pass
    return (0, 0), memory
