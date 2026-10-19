
import random
import copy
import numpy as np

# Directions for checking lines (dx, dy)
DIRS = [
    (0, 1),   # horizontal
    (1, 0),   # vertical
    (1, 1),   # diagonal \ (down‑right)
    (1, -1)   # diagonal / (down‑left)
]

def _has_winning_move(board: list[list[int]]) -> int | None:
    """
    Returns a column index where dropping our piece creates a line of four.
    None if no winning move exists.
    """
    for col in range(7):
        if board[0][col] != 0:  # column not empty
            continue
        # Simulate the drop
        sim = copy.deepcopy(board)
        row = 5
        while row >= 0 and sim[row][col] != 0:
            row -= 1
        sim[row][col] = 1  # our piece
        if _is_win(sim):
            return col
    return None


def _is_win(board: list[list[int]]) -> bool:
    """
    Checks whether board contains a line of four of our discs (value 1).
    Returns True if any win exists.
    """
    # Quick early exit: scan only rows below the highest disc we own
    # (rows with at least one 1)
    for r in range(6):
        if any(board[r][c] == 1 for c in range(7)):
            # Check all lines that intersect this row
            for c in range(7):
                # Horizontal
                if c <= 3:
                    if board[r][c] == board[r][c+1] == board[r][c+2] == board[r][c+3] == 1:
                        return True
                # Vertical
                if r <= 2:
                    if board[r][c] == board[r+1][c] == board[r+2][c] == board[r+3][c] == 1:
                        return True
                # Diagonal /
                if c <= 3 and r <= 2:
                    if board[r][c] == board[r+1][c-1] == board[r+2][c-2] == board[r+3][c-3] == 1:
                        return True
                # Diagonal \
                if c <= 3 and r <= 2:
                    if board[r][c] == board[r+1][c+1] == board[r+2][c+2] == board[r+3][c+3] == 1:
                        return True
    return False


def _opponent_win(board: list[list[int]]) -> int | None:
    """
    Returns a column index where the opponent could win on their next turn.
    None if they have no winning move.
    """
    for col in range(7):
        if board[0][col] != 0:
            continue
        sim = copy.deepcopy(board)
        row = 5
        while row >= 0 and sim[row][col] != 0:
            row -= 1
        sim[row][col] = -1  # opponent disc
        if _is_win(sim):
            return col
    return None


def _heuristic_score(board: list[list[int]], col: int) -> int:
    """
    Simulates dropping our piece in `col` and returns a heuristic score:
    - +10 for each line where we have exactly three of our discs and one empty.
    - +1 for each line where we have exactly two of our discs and two empty slots
      (this can become an open three after another move).
    Lines containing opponent discs (-1) are ignored.
    """
    # Make a copy and drop our piece
    sim = copy.deepcopy(board)
    row = 5
    while row >= 0 and sim[row][col] != 0:
        row -= 1
    sim[row][col] = 1

    # Evaluate lines
    total = 0

    # Horizontal lines
    for r in range(6):
        for c in range(4):
            line = [sim[r][c + dr] for dr in range(-3, 4)]
            # We need contiguous cells; only consider sequences where they are side‑by‑side
            if c + 4 > 7:  # out of bounds
                break
            line_vals = [sim[r][c + dx] for dx, dy in [(0, 0), (0, 1), (0, 2), (0, 3)]]
            # Combine with opponent check
            if any(v == -1 for v in line_vals):
                continue
            count_ones = sum(1 for v in line_vals if v == 1)
            if count_ones == 3:
                total += 10
            elif count_ones == 2:
                total += 1

    # Vertical lines
    for c in range(7):
        for r in range(3):  # rows 0‑3 inclusive
            line_vals = [sim[r + dr][c] for dr in range(-3, 4) if 0 <= r + dr <= 5]
            # Using shift: start at highest occupied row, go downwards
            if any(v == -1 for v in line_vals):
                continue
            count_ones = sum(1 for v in line_vals if v == 1)
            if count_ones == 3:
                total += 10
            elif count_ones == 2:
                total += 1

    # Diagonal / (down‑left)
    for c in range(4):
        for r in range(3):
            line_vals = [
                sim[r + dr][c - dr]  # start at top‑right then go down‑left
                for dr in range(-3, 4)
                if 0 <= r + dr <= 5 and 0 <= c - dr <= 6
            ]
            if any(v == -1 for v in line_vals):
                continue
            count_ones = sum(1 for v in line_vals if v == 1)
            if count_ones == 3:
                total += 10
            elif count_ones == 2:
                total += 1

    # Diagonal \ (down‑right)
    for c in range(4):
        for r in range(3):
            line_vals = [
                sim[r + dr][c + dr]  # down‑right
                for dr in range(-3, 4)
                if 0 <= r + dr <= 5 and 0 <= c + dr <= 6
            ]
            if any(v == -1 for v in line_vals):
                continue
            count_ones = sum(1 for v in line_vals if v == 1)
            if count_ones == 3:
                total += 10
            elif count_ones == 2:
                total += 1

    return total


def policy(board: list[list[int]]) -> int:
    """
    Main API. Returns a legal column index (0‑6) for the current player.
    """
    # 1️⃣ Check for immediate win
    win_col = _has_winning_move(board)
    if win_col is not None:
        return win_col

    # 2️⃣ Block opponent if they have a forced win
    opp_win_col = _opponent_win(board)
    if opp_win_col is not None:
        # Simulate the same column; after dropping our piece it will block
        row = 5
        while row >= 0 and board[row][opp_win_col] != 0:
            row -= 1
        # The column is non‑full, guaranteed by the previous check
        return opp_win_col

    # 3️⃣ Heuristic search – evaluate all columns with an empty cell
    candidate_cols = [col for col in range(7) if board[0][col] == 0]

    # Score columns
    col_scores = [(col, _heuristic_score(board, col)) for col in candidate_cols]

    # Sort by score (descending) and then by column index (ascending) for deterministic tie‑break
    col_scores.sort(key=lambda x: (-x[1], x[0]))

    best_col, best_score = col_scores[0]

    return best_col


# End of file
