
import random
from typing import List, Tuple

# Pre‑compute the eight winning lines of a 3×3 board.
_LINES = [
    [(0, 0), (0, 1), (0, 2)],  # rows
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],  # columns
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],  # diagonals
    [(0, 2), (1, 1), (2, 0)],
]

def _winning_move(board: List[List[int]]) -> None:
    """Return a cell that completes a line of our own marks, if any."""
    for line in _LINES:
        ours = [cell for cell in line if board[cell[0]][cell[1]] == 1]
        if len(ours) == 2:
            # The remaining cell must be unknown (0) – otherwise the line is already full.
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)
    return None

def _block_score(board: List[List[int]]) -> Tuple[Tuple[int, int], int]:
    """
    For each unknown cell compute how many opponent‑only lines (lines with no
    confirmed our marks) pass through it.  Return the best cell together
    with its score.
    """
    best_cell = None
    best_score = -1

    # Pre‑compute which lines are “pure opponent” (no of‑ours cells).
    pure_lines = [line for line in _LINES if all(board[r][c] != 1 for r, c in line)]

    # Count each unknown cell.
    for r in range(3):
        for c in range(3):
            if board[r][c] != 0:
                continue
            score = sum(1 for line in pure_lines if (r, c) in line)
            if score > best_score or (score == best_score and (best_cell is None or (r, c) < best_cell)):
                best_score = score
                best_cell = (r, c)

    # In the unlikely case every cell is already ours (full board), fall back.
    if best_cell is None:
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return ((r, c), 0)
        # board full – return (0,0) as a legal dummy move
        return ((0, 0), 0)

    return best_cell, best_score

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next move for Phantom Tic‑Tac‑Toe.

    Parameters
    ----------
    board : list[list[int]]
        3×3 board where 1 = our confirmed mark, 0 = unknown (empty or opponent).

    Returns
    -------
    tuple[int, int]
        (row, col) of the cell we attempt to mark.
    """
    # 1. Try to win immediately.
    win = _winning_move(board)
    if win is not None:
        return win

    # 2. Otherwise pick the cell that blocks the most potential opponent lines.
    best_cell, _ = _block_score(board)
    return best_cell
