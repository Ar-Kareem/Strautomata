
import numpy as np
import random
from typing import List, Tuple

SIZE = 6
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1), (1, 0), (1, 1)]

def queen_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Queen (max‑abs) distance."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

def reachable_dests(src: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Return all empty squares reachable from src in a straight queen line."""
    sr, sc = src
    dests = []
    for dr, dc in DIRS:
        step = 1
        while True:
            nr, nc = sr + dr * step, sc + dc * step
            if not (0 <= nr < SIZE and 0 <= nc < SIZE):
                break
            # path check: all squares from src+dr up to nr,nc must be empty
            path_ok = True
            for i in range(step):
                r_i, c_i = sr + dr * (i + 1), sc + dc * (i + 1)
                if not (0 <= r_i < SIZE and 0 <= c_i < SIZE) or board[r_i, c_i] != 0:
                    path_ok = False
                    break
            if not path_ok or board[nr, nc] != 0:
                break
            dests.append((nr, nc))
            step += 1
    return dests

def reachable_arrows(dest: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Return every empty square that can be shot from dest."""
    tr, tc = dest
    arrows = []
    for ar, ac in DIRS:
        if ar == 0 and ac == 0:
            continue
        arrow_step = 1
        while True:
            rarr, carr = tr + ar * arrow_step, tc + ac * arrow_step
            if not (0 <= rarr < SIZE and 0 <= carr < SIZE):
                break
            if board[rarr, carr] != 0:
                break
            arrows.append((rarr, carr))
            arrow_step += 1
    return arrows

def legal_moves(board: np.ndarray) -> List[Tuple[Tuple[int,int], Tuple[int,int], Tuple[int,int], int]]:
    """Enumerate all legal Amazon moves with a heuristic score."""
    board = np.asarray(board)
    # own and opponent positions
    my_pos = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r, c] == 1]
    opp_pos = {(r, c) for r, c in my_pos if board[r, c] == 2}
    if not my_pos:
        raise RuntimeError("No legal moves found (should never happen).")
    legal = []
    for src in my_pos:
        for dest in reachable_dests(src):
            # arrow possibilities from dest
            for arrow in reachable_arrows(dest):
                # evaluate the move
                new_my = set(my_pos) - {src} | {dest}
                # distance contributed by the moved Amazon
                d_my = min(queen_distance(pos, nearest) for pos in new_my
                           for nearest in opp_pos)
                # distance contributed by the arrow
                d_arrow = min(queen_distance(pos, nearest) for nearest in opp_pos
                              for pos in {arrow})
                # weighted sum: arrow distance 5× more important
                score = -(d_my + 5 * d_arrow)
                legal.append((src, dest, arrow, score))
    return legal

def policy(board):
    """Return a legal move string: \"from,to:arrow\" (zero‑indexed, comma‑separated)."""
    moves = legal_moves(board)
    if not moves:
        raise RuntimeError("No legal move could be generated.")
    # pick the best move; break ties randomly
    best = max(moves, key=lambda x: x[3])
    (src, dest, arrow, _) = best
    return f"{src[0]},{src[1]}:{dest[0]},{dest[1]}:{arrow[0]},{arrow[1]}"
