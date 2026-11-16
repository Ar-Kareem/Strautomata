
#!/usr/bin/env python3
"""
Connect‑4 targeting policy.

The module defines a single function:

    def policy(board: list[list[int]]) -> int:
        ...

The function receives a 6×7 board (list of 6 rows, each row a list of 7 ints)
with the encoding:
    0  – empty,
    1  – our disc (the player invoking the policy),
   -1  – opponent's disc.

It returns the column (0‑6) where we should drop our disc.
"""

from __future__ import annotations
import copy
from typing import List, Optional

ROWS = 6
COLS = 7

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def drop_row(board: List[List[int]], col: int) -> Optional[int]:
    """
    Return the row index where a disc would land if dropped in ``col``.
    Rows are indexed from top (0) to bottom (ROWS‑1).  Returns None if the
    column is full.
    """
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def check_win(board: List[List[int]], player: int) -> bool:
    """
    Return True if ``player`` (1 or -1) has four in a row anywhere on the board.
    """
    # Directions: (dr, dc)
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != player:
                continue
            for dr, dc in directions:
                cnt = 1
                rr, cc = r + dr, c + dc
                while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
                    cnt += 1
                    if cnt == 4:
                        return True
                    rr += dr
                    cc += dc
    return False


def simulate(board: List[List[int]], col: int, player: int) -> Optional[List[List[int]]]:
    """
    Return a deep copy of ``board`` with ``player``'s disc dropped in ``col``.
    If the column is full, return None.
    """
    row = drop_row(board, col)
    if row is None:
        return None
    new_board = copy.deepcopy(board)
    new_board[row][col] = player
    return new_board


def safe_columns(board: List[List[int]]) -> List[int]:
    """Return a list of column indices that are not full."""
    return [c for c in range(COLS) if drop_row(board, c) is not None]

# ----------------------------------------------------------------------
# Policy implementation
# ----------------------------------------------------------------------
def policy(board: List[List[int]]) -> int:
    """
    Choose a column to drop our disc.

    Strategy:
        1. Win if possible.
        2. Block opponent's immediate win.
        3. Avoid moves that give the opponent an immediate win.
        4. Play the best column according to a static ordering.
    """
    our_player = 1
    opp_player = -1

    # 1. Winning move
    for col in safe_columns(board):
        sim = simulate(board, col, our_player)
        if sim is not None and check_win(sim, our_player):
            return col

    # 2. Block opponent win
    for col in safe_columns(board):
        sim = simulate(board, col, opp_player)
        if sim is not None and check_win(sim, opp_player):
            return col

    # 3. Avoid giving opponent a win next turn
    candidate_cols = []
    for col in safe_columns(board):
        # Simulate our move
        sim_our = simulate(board, col, our_player)
        if sim_our is None:
            continue

        # Now check if opponent has any winning response
        opponent_can_win = False
        for opp_col in safe_columns(sim_our):
            sim_opp = simulate(sim_our, opp_col, opp_player)
            if sim_opp is not None and check_win(sim_opp, opp_player):
                opponent_can_win = True
                break
        if not opponent_can_win:
            candidate_cols.append(col)

    # If we have safe columns (that don't hand the opponent a win) use them,
    # otherwise fall back to any legal move.
    if candidate_cols:
        safe_move_pool = candidate_cols
    else:
        safe_move_pool = safe_columns(board)

    # 4. Heuristic ordering – centre column is strongest.
    ordering = [3, 2, 4, 1, 5, 0, 6]
    for preferred in ordering:
        if preferred in safe_move_pool:
            return preferred

    # Fallback (should never happen if board not full)
    return safe_move_pool[0]

# ----------------------------------------------------------------------
# Optional: quick self‑test when run as script
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple sanity check: empty board -> centre column
    empty_board = [[0] * COLS for _ in range(ROWS)]
    print("Chosen column on empty board:", policy(empty_board))
