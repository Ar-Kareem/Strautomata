
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next cell to attempt in Phantom Tic‑Tac‑Toe.

    Parameters
    ----------
    board : list[list[int]]
        3×3 matrix where 1 marks a cell we already own, 0 marks an
        unknown cell (could be empty or opponent‑occupied).

    Returns
    -------
    (row, col) : tuple[int, int]
        Coordinates of the cell we will attempt to claim.
    """

    # All possible winning lines (rows, columns, diagonals)
    lines = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    # ------------------------------------------------------------------
    # 1. Immediate winning move: if we already have two confirmed marks,
    #    try to claim the third cell of that line.
    # ------------------------------------------------------------------
    for line in lines:
        ours = sum(board[r][c] for r, c in line)
        if ours == 2:
            # the third cell must be unknown (0) – attempt it
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)

    # ------------------------------------------------------------------
    # 2. Compute heuristic scores for all unknown cells.
    # ------------------------------------------------------------------
    # Base values: centre > corners > edges
    base_score = [
        [2, 1, 2],
        [1, 3, 1],
        [2, 1, 2],
    ]

    scores = [[0] * 3 for _ in range(3)]

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:          # only consider cells we don't own yet
                scores[r][c] = base_score[r][c]

    # Bonus for cells that lie on lines where we already have a mark.
    for line in lines:
        line_ours = sum(board[r][c] for r, c in line)
        if line_ours > 0:
            for r, c in line:
                if board[r][c] == 0:
                    scores[r][c] += 1  # encourage building the line

    # ------------------------------------------------------------------
    # 3. Choose the best cell(s); break ties randomly.
    # ------------------------------------------------------------------
    # Gather all candidate cells with maximal score.
    max_score = -1
    candidates = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:          # must be a legal move
                s = scores[r][c]
                if s > max_score:
                    max_score = s
                    candidates = [(r, c)]
                elif s == max_score:
                    candidates.append((r, c))

    # Fallback – should never happen, but ensures a legal move.
    if not candidates:
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)

    return random.choice(candidates)
