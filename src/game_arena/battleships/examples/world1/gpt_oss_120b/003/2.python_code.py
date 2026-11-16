
#!/usr/bin/env python3
"""
Battleship targeting policy.

The module provides a single function `policy(board)` that returns the next
coordinates (row, col) to fire at, given the current knowledge of the opponent
grid.

The algorithm builds a probability map by counting all ship placements that
are consistent with the observed hits and misses, then chooses the unknown
cell with the highest count.
"""

from __future__ import annotations
import random
from typing import List, Tuple

# Original fleet composition (lengths of the ships)
_SHIP_LENGTHS = [5, 4, 3, 3, 2]
_BOARD_SIZE = 10


def _legal_placements(board: List[List[int]], length: int) -> List[Tuple[int, int, bool]]:
    """
    Generate all legal placements for a ship of the given length.

    Each placement is represented as a tuple (row, col, horizontal) where
    (row, col) is the starting cell (top‑leftmost for horizontal, topmost for
    vertical) and `horizontal` is True for a horizontal ship.

    A placement is legal if:
        * It stays inside the 10 × 10 board.
        * It does not overlap a known miss (-1).
        * It may overlap hits (1) – those are allowed.
    """
    placements = []
    N = _BOARD_SIZE

    # Horizontal placements
    for r in range(N):
        for c in range(N - length + 1):
            ok = True
            for k in range(length):
                if board[r][c + k] == -1:  # miss – cannot be part of a ship
                    ok = False
                    break
            if ok:
                placements.append((r, c, True))

    # Vertical placements
    for r in range(N - length + 1):
        for c in range(N):
            ok = True
            for k in range(length):
                if board[r + k][c] == -1:
                    ok = False
                    break
            if ok:
                placements.append((r, c, False))

    return placements


def _score_board(board: List[List[int]]) -> List[List[int]]:
    """
    Build a score matrix where each unknown cell contains the number of
    ship placements that could occupy it, given the current knowledge.
    """
    N = _BOARD_SIZE
    # Initialize all scores to zero
    scores = [[0 for _ in range(N)] for _ in range(N)]

    for length in _SHIP_LENGTHS:
        for r, c, horiz in _legal_placements(board, length):
            # Increment score for every unknown cell covered by this placement
            for k in range(length):
                rr = r + (0 if horiz else k)
                cc = c + (k if horiz else 0)
                if board[rr][cc] == 0:          # unknown cell only
                    scores[rr][cc] += 1

    return scores


def _choose_best(scores: List[List[int]], board: List[List[int]]) -> Tuple[int, int]:
    """
    From the scores matrix, pick the unknown cell with the highest score.
    Random tie‑breaking is applied to avoid deterministic behavior.
    """
    best_cells = []
    best_score = -1
    N = _BOARD_SIZE

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:          # skip already tried cells
                continue
            s = scores[r][c]
            if s > best_score:
                best_score = s
                best_cells = [(r, c)]
            elif s == best_score:
                best_cells.append((r, c))

    # Fallback: if for some reason there is no unknown cell (should not happen)
    if not best_cells:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        raise RuntimeError("No valid cells to fire at.")

    return random.choice(best_cells)


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Given the current board knowledge, return the coordinates (row, col)
    of the next shot.

    Parameters
    ----------
    board : list[list[int]]
        10 × 10 grid where
            0  – unknown,
           -1  – miss,
            1  – hit.

    Returns
    -------
    tuple[int, int]
        Row and column indices (0‑based) of the chosen target.
    """
    # Defensive copy is not needed – we only read the board.
    scores = _score_board(board)
    row, col = _choose_best(scores, board)
    return (row, col)


# If this file is executed directly, run a tiny demo.
if __name__ == "__main__":
    # Simple demo: empty board – should fire on a parity cell.
    empty_board = [[0] * _BOARD_SIZE for _ in range(_BOARD_SIZE)]
    r, c = policy(empty_board)
    print(f"Chosen shot on empty board: ({r}, {c})")
