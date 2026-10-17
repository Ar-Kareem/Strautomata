
import numpy as np
from typing import List

# -------------------------------------------------------------
# Helper data structures
# -------------------------------------------------------------
quadrant_offsets = {
    0: (0, 0),   # top‑left
    1: (0, 3),   # top‑right
    2: (3, 0),   # bottom‑left
    3: (3, 3),   # bottom‑right
}

# -------------------------------------------------------------
# Core game utilities
# -------------------------------------------------------------
def rotate(board: np.ndarray, quad: int, direction: str) -> np.ndarray:
    """
    Rotate the 3×3 sub‑board of `board` clockwise ('R') or anticlockwise ('L').
    Returns a new board without modifying the input.
    """
    b = np.array(board, copy=True)
    r0, c0 = quadrant_offsets[quad]
    sub = b[r0:r0+3, c0:c0+3]
    if direction == 'L':
        sub = np.rot90(sub, 1)    # anticlockwise
    else:  # direction == 'R'
        sub = np.rot90(sub, -1)   # clockwise
    b[r0:r0+3, c0:c0+3] = sub
    return b


def has_five(board: np.ndarray, player_val: int) -> bool:
    """
    Return True if `player_val` (1 for us, 2 for opponent) has a line of length ≥5.
    The board may be 3‑D; we use the flattened 6×6 plane.
    """
    # Horizontal
    for row in range(6):
        for col_start in range(0, 2):
            if np.all(board[row, col_start:col_start+5] == player_val):
                return True

    # Vertical
    for col in range(6):
        for row_start in range(0, 2):
            if np.all(board[row_start:row_start+5, col] == player_val):
                return True

    # Main diagonal (top‑left to bottom‑right)
    for row in range(0, 2):
        for col in range(0, 2):
            if np.all(board[row:row+5, col:col+5] == player_val):
                return True

    # Anti diagonal (top‑right to bottom‑left)
    for row in range(0, 2):
        for col in range(4, 6):
            if np.all(board[row:row+5, col-4:col+1] == player_val):
                return True

    return False


def open_end_count(board: np.ndarray, player_val: int) -> int:
    """
    Count empty squares that can extend any contiguous block of `player_val`.
    The function marks cells as visited to avoid double‑counting.
    """
    visited = np.zeros_like(board, dtype=bool)
    count = 0

    # ----- Horizontal -----
    for r in range(6):
        c = 0
        while c < 6:
            if board[r, c] == player_val and not visited[r, c]:
                start = c
                length = 0
                while (c < 6 and board[r, c] == player_val and not visited[r, c]):
                    c += 1
                    length += 1
                c -= 1               # last increment was out of the block
                end = start + length - 1

                # left side
                if start > 0 and board[r, start - 1] == 0:
                    count += 1
                # right side
                if end < 5 and board[r, end + 1] == 0:
                    count += 1

                # mark the block as visited
                for i in range(start, end + 1):
                    visited[r, i] = True
            else:
                c += 1

    # ----- Vertical -----
    for c in range(6):
        r = 0
        while r < 6:
            if board[r, c] == player_val and not visited[r, c]:
                start = r
                length = 0
                while (r < 6 and board[r, c] == player_val and not visited[r, c]):
                    r += 1
                    length += 1
                r -= 1
                end = start + length - 1

                # up side
                if start > 0 and board[start - 1, c] == 0:
                    count += 1
                # down side
                if end < 5 and board[end + 1, c] == 0:
                    count += 1

                for i in range(start, end + 1):
                    visited[i, c] = True
            else:
                r += 1

    # ----- Main diagonal (↘) -----
    for r in range(0, 3):
        for c in range(0, 3):
            if board[r, c] == player_val and not visited[r, c]:
                length = 0
                while (r + length < 6 and c + length < 6
                       and board[r + length, c + length] == player_val
                       and not visited[r + length, c + length]):
                    length += 1
                # open‑end up‑left
                if r > 0 and c > 0 and board[r - 1, c - 1] == 0:
                    count += 1
                # open‑end down‑right
                if r + length - 1 < 5 and c + length - 1 < 5:
                    count += 1

                for i in range(length):
                    visited[r + i, c + i] = True

    # ----- Anti diagonal (↙) -----
    for r in range(0, 3):
        for c in range(4, 6):
            if board[r, c] == player_val and not visited[r, c]:
                length = 0
                while (r + length < 6 and c - length >= 0
                       and board[r + length, c - length] == player_val
                       and not visited[r + length, c - length]):
                    length += 1
                # open‑end up‑right
                if r > 0 and c + length < 6 and board[r - 1, c + length] == 0:
                    count += 1
                # open‑end down‑left
                if r + length < 6 and c > 0 and board[r + length, c - 1] == 0:
                    count += 1

                for i in range(length):
                    visited[r + i, c - i] = True

    return count


def quadrant_counts(board: np.ndarray) -> np.ndarray:
    """
    Return a length‑4 array with the total number of stones in each 3×3 quadrant.
    """
    out = np.zeros(4, dtype=int)
    for q in range(4):
        r0, c0 = quadrant_offsets[q]
        out[q] = board[r0:r0+3, c0:c0+3].sum()
    return out


# -------------------------------------------------------------
# Heuristic evaluation
# -------------------------------------------------------------
def evaluate(board: np.ndarray, opponent_board: np.ndarray) -> int:
    """
    Return an integer score for the board after a move has been applied.
    Higher is better.
    """
    # combine the two 2‑D boards into a 3‑D board: 1 = us, 2 = them
    combined = np.stack([board, opponent_board], axis=-1)

    # Immediate win detection (we already filter earlier, but keep as safety)
    if has_five(combined, 1):
        return 10000
    if has_five(combined, 2):
        return -10000

    # Open‑ends for each player
    our_open = open_end_count(combined, 1)
    their_open = open_end_count(combined, 2)

    # Center (the 2×2 square) – bonus/penalty
    center_score = 0
    for i, j in [(2, 2), (2, 3), (3, 2), (3, 3)]:
        if combined[i, j, 0] == 1:
            center_score += 5
        elif combined[i, j, 1] == 2:
            center_score -= 5

    # Corners – bonus/penalty
    corner_score = 0
    for i, j in [(0, 0), (0, 5), (5, 0), (5, 5)]:
        if combined[i, j, 0] == 1:
            corner_score += 3
        elif combined[i, j, 1] == 2:
            corner_score -= 3

    # Quadrant balance (our stones minus theirs in each quadrant)
    my_counts = quadrant_counts(combined[..., 0])
    their_counts = quadrant_counts(combined[..., 1])
    quad_balance = np.sum(my_counts - their_counts)

    # Heuristic: open‑ends are worth a little, centre a lot, etc.
    score = (our_open * 2) - (their_open * 2) \
            + center_score * 10 \
            + corner_score * 5 \
            + quad_balance
    return score


# -------------------------------------------------------------
# Main policy
# -------------------------------------------------------------
def policy(you: List[List[int]] | np.ndarray,
           opponent: List[List[int]] | np.ndarray) -> str:
    """
    Return the best legal move as a string `"row,col,quad,dir"`.
    The function is guaranteed to return a legal move.
    """
    # Accept both list-of-lists and numpy arrays
    you_np = np.array(you, dtype=int)
    opp_np = np.array(opponent, dtype=int)

    # Verify board size
    if you_np.shape != (6, 6) or opp_np.shape != (6, 6):
        raise ValueError("Both `you` and `opponent` must be 6×6 boards.")

    # All empty cells where we can place our marble
    empties = [(r, c) for r in range(6) for c in range(6)
               if you_np[r, c] == 0 and opp_np[r, c] == 0]

    # Heuristic weights (feel‑free to tune)
    OPEN_WEIGHT = 2
    CENTER_WEIGHT = 10
    CORNER_WEIGHT = 5
    QUAD_WEIGHT = 1

    best_score = float("-inf")
    best_move = None

    for r, c in empties:
        for quad in range(4):
            for direction in ("L", "R"):
                # 1️⃣ Place our marble
                new_you = you_np.copy()
                new_you[r, c] = 1

                # 2️⃣ Rotate both sub‑boards
                rotated_you = rotate(new_you, quad, direction)
                rotated_opp = rotate(opp_np, quad, direction)

                # 3️⃣ Combine the two planes for evaluation
                #   channel 0 → our stones, channel 1 → opponent's stones
                combined = np.stack([rotated_you, rotated_opp], axis=-1)

                # 4️⃣ Immediate win detection – we return instantly
                if has_five(combined, 1):
                    return f"{r+1},{c+1},{quad},{direction}"

                # 5️⃣ Score this move
                score = evaluate(combined, rotated_opp)

                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)

    # Fallback – should never be triggered because the board is always non‑full,
    # but we keep it to guarantee a legal move.
    if best_move is None:
        # pick the first empty cell with any rotation
        r, c = empties[0]
        quad, direction = 0, "L"
        best_move = (r, c, quad, direction)

    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
