
import numpy as np
import random

# static positional weights – higher is better
_POS_WEIGHT = np.array([
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100],
], dtype=int)

_DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
               ( 0, -1),          ( 0, 1),
               ( 1, -1), ( 1, 0), ( 1, 1)]

def _on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _flips_for_move(r, c, you, opponent):
    """Return list of positions that would be flipped if we play at (r,c)."""
    flips = []
    for dr, dc in _DIRECTIONS:
        cur_r, cur_c = r + dr, c + dc
        line = []
        while _on_board(cur_r, cur_c) and opponent[cur_r, cur_c] == 1:
            line.append((cur_r, cur_c))
            cur_r += dr
            cur_c += dc
        if line and _on_board(cur_r, cur_c) and you[cur_r, cur_c] == 1:
            flips.extend(line)
    return flips

def _legal_moves(you, opponent):
    """Yield (r,c,flips) for every legal move for the player `you`."""
    empty = np.logical_not(np.logical_or(you, opponent))
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            flips = _flips_for_move(r, c, you, opponent)
            if flips:                     # at least one direction flips
                yield (r, c, flips)

def _to_alg(r, c):
    """Convert board indices to algebraic notation (e.g., (3,0) -> 'a4')."""
    file = chr(ord('a') + c)
    rank = str(r + 1)               # rows are 1‑based
    return file + rank

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the best legal move for `you` given the current board.
    If no move is possible, return "pass".
    """
    best_score = -float('inf')
    best_moves = []   # list of (r,c) with the same best_score

    for r, c, flips in _legal_moves(you, opponent):
        # simple evaluation: flips + positional weight
        score = len(flips) + _POS_WEIGHT[r, c]
        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))

    if not best_moves:                     # no legal move
        return "pass"

    # pick a random move among equally good candidates
    chosen_r, chosen_c = random.choice(best_moves)
    return _to_alg(chosen_r, chosen_c)
