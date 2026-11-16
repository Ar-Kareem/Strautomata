
import numpy as np
import random
from typing import List, Tuple

# Pre‑computed set of all 5‑in‑a‑row lines (0‑based coordinates)
_HORIZONTAL = [(r, c + i) for i in range(5) for r in range(6) for c in (range(0, 4))]
_VERTICAL   = [(r + i, c) for i in range(5) for r in (range(0, 4)) for c in range(6)]
_DIAG_MAIN   = [(r + i, c + i) for i in range(5) for r in range(4) for c in range(4)]
_DIAG_ANTI   = [(r + i, c - i) for i in range(5) for r in range(4) for c in (range(4, 6))]

_LINES: List[Tuple[Tuple[int, int], ...]] = list(
    set(_HORIZONTAL + _VERTICAL + _DIAG_MAIN + _DIAG_ANTI)
)

def _rotate(board: np.ndarray, row_start: int, col_start: int, direction: str) -> None:
    """
    Rotate a 3×3 quadrant inside `board`.
    `direction` – 'L' for anticlockwise, 'R' for clockwise.
    """
    sub = board[row_start:row_start + 3, col_start:col_start + 3]
    if direction == 'L':
        sub = np.rot90(sub, k=1)   # anticlockwise
    else:  # 'R'
        sub = np.rot90(sub, k=3)   # clockwise
    board[row_start:row_start + 3, col_start:col_start + 3] = sub

def _evaluate(
    you: np.ndarray, opp: np.ndarray
) -> Tuple[bool, bool, int, int]:
    """
    Return a tuple:
    - you_win (bool)
    - opp_win (bool)
    - our_4_line_count (int)
    - opp_4_line_count (int)
    """
    you_win = False
    opp_win = False
    our_4 = 0
    opp_4 = 0
    for line_coords in _LINES:
        # Convert line coordinates to array of (r,c) pairs
        try:
            you_vals = [you[r, c] for r, c in line_coords]
            opp_vals = [opp[r, c] for r, c in line_coords]
        except IndexError:
            continue  # board indexing mistake; should never happen
        our_score = you_vals.count(1)
        opp_score = opp_vals.count(1)
        if our_score == 5:
            you_win = True
        if opp_score == 5:
            opp_win = True
        if our_score >= 4:
            our_4 += 1
        if opp_score >= 4:
            opp_4 += 1
    return you_win, opp_win, our_4, opp_4

def _quadrant_bounds(q: int) -> Tuple[int, int, int, int]:
    """Return (row_start, row_end, col_start, col_end) for quadrant q."""
    group = q // 2          # 0 = top half, 1 = bottom half
    row_start = group * 3
    col_start = (q % 2) * 3
    # Use inclusive start, exclusive end
    return row_start, row_start + 3, col_start, col_start + 3

def policy(you: List[List[int]] | np.ndarray,
          opponent: List[List[int]] | np.ndarray) -> str:
    """
    Return a legal move string: "row,col,quad,dir".
    `row` and `col` are 1‑indexed; `quad` is 0‑4; `dir` is 'L' or 'R'.
    """
    # Convert to numpy for easy slicing and copying
    if isinstance(you, list):
        you_np = np.array(you, dtype=int)
    else:
        you_np = you.copy()
    if isinstance(opponent, list):
        opp_np = np.array(opponent, dtype=int)
    else:
        opp_np = opponent.copy()

    # Find all empty cells
    empty_cells: List[Tuple[int, int]] = [
        (r, c)
        for r in range(6)
        for c in range(6)
        if you_np[r, c] == 0 and opp_np[r, c] == 0
    ]

    best_move: Tuple[int, int, int, str] = None
    best_heuristic = -float('inf')
    best_quad_dir_heuristic = 0

    for row, col in empty_cells:
        # Cycle through each quadrant and direction
        for quad in range(4):
            row_start, row_end, col_start, col_end = _quadrant_bounds(quad)
            for direction in ('L', 'R'):
                # Deep copy to avoid mutating the original boards
                you_try = you_np.copy()
                opp_try = opp_np.copy()

                # Placement
                you_try[row, col] = 1

                # Rotation
                _rotate(you_try, row_start, col_start, direction)
                _rotate(opp_try, row_start, col_start, direction)

                you_win, opp_win, our_4, opp_4 = _evaluate(you_try, opp_try)

                # Heuristic: wins first, then line advantage
                if you_win:
                    heuristic = 1e9
                elif opp_win:
                    heuristic = -1e9
                else:
                    heuristic = our_4 - opp_4

                # Update best move if strictly better, else random tie‑break
                if heuristic > best_heuristic:
                    best_heuristic = heuristic
                    best_move = (row, col, quad, direction)
                elif heuristic == best_heuristic:
                    # Random tie‑break – 50 % chance to replace current best
                    if random.random() < 0.5:
                        best_move = (row, col, quad, direction)

    # Convert the best move back to the required 1‑indexed string format
    row_out, col_out, quad_out, dir_out = best_move
    return f"{row_out + 1},{col_out + 1},{quad_out},{dir_out}"
