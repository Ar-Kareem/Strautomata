
#!/usr/bin/env python3
"""
Simple Connect‑4 targeting policy.

The board is a 6x7 list of lists:
    0  → empty
    1  → our disc (the player calling `policy`)
   -1  → opponent disc

Rows are indexed top‑to‑bottom (0‑5), columns left‑to‑right (0‑6).

The function `policy(board)` returns a column index (0‑6) where we should drop
our disc.  It always selects a non‑full column.
"""

from typing import List, Tuple

ROWS = 6
COLS = 7
PLAYER = 1
OPPONENT = -1


def available_columns(board: List[List[int]]) -> List[int]:
    """Return a list of column indices that are not full."""
    return [c for c in range(COLS) if board[0][c] == 0]


def apply_move(board: List[List[int]], col: int, player: int) -> Tuple[List[List[int]], int]:
    """
    Return a new board with `player`'s disc dropped in `col`
    and the row index where it landed.
    """
    new_board = [row[:] for row in board]  # shallow copy of each row
    for row in range(ROWS - 1, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            return new_board, row
    raise ValueError("apply_move called on a full column")


def count_consecutive(board: List[List[int]], start_row: int, start_col: int,
                      d_row: int, d_col: int, player: int) -> int:
    """Count consecutive `player` discs from (start_row, start_col) in the given direction."""
    count = 0
    r, c = start_row, start_col
    while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
        count += 1
        r += d_row
        c += d_col
    return count


def is_winning_move(board: List[List[int]], row: int, col: int, player: int) -> bool:
    """Check whether placing `player` at (row, col) creates a connect‑4."""
    # Directions: horizontal, vertical, diag \, diag /
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        # Count discs in both positive and negative direction, subtract 1 to avoid double‑counting the placed disc.
        total = (count_consecutive(board, row, col, dr, dc, player) +
                 count_consecutive(board, row, col, -dr, -dc, player) - 1)
        if total >= 4:
            return True
    return False


def policy(board: List[List[int]]) -> int:
    """
    Choose a column to drop our disc.

    Strategy:
    1. Win if possible.
    2. Block opponent's immediate win.
    3. Pick the most central available column.
    """
    valid_cols = available_columns(board)
    if not valid_cols:
        raise RuntimeError("No valid moves available")

    # 1. Check for immediate winning moves.
    for col in valid_cols:
        temp_board, row = apply_move(board, col, PLAYER)
        if is_winning_move(temp_board, row, col, PLAYER):
            return col

    # 2. Block opponent's immediate winning moves.
    for col in valid_cols:
        temp_board, row = apply_move(board, col, OPPONENT)
        if is_winning_move(temp_board, row, col, OPPONENT):
            return col

    # 3. Prefer central columns.
    centre_order = [3, 2, 4, 1, 5, 0, 6]  # heuristic ordering from most to least central
    for col in centre_order:
        if col in valid_cols:
            return col

    # Fallback (should never happen because of earlier check)
    return valid_cols[0]


# If this file is executed directly, run a simple sanity test.
if __name__ == "__main__":
    empty_board = [[0] * COLS for _ in range(ROWS)]
    print("Chosen column on empty board:", policy(empty_board))
