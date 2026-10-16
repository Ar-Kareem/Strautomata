
import numpy as np
import random
import math
from typing import List, Tuple

def find_empty_cells(you: np.ndarray, opp: np.ndarray) -> List[Tuple[int, int]]:
    """Return all cells where both players have an empty spot (0 in both)."""
    empties = []
    for i in range(6):
        for j in range(6):
            if you[i, j] == 0 and opp[i, j] == 0:
                empties.append((i, j))
    return empties


def longest_consecutive(board: np.ndarray) -> int:
    """Return the length of the longest straight line of your marbles."""
    best = 0
    # Directions: horizontal, vertical, diag \ and diag /
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                continue
            for dr, dc in dirs:
                cnt = 1
                rr, cc = r + dr, c + dc
                while 0 <= rr < 6 and 0 <= cc < 6 and board[rr, cc] == 1:
                    cnt += 1
                    if cnt >= 5:
                        break
                    rr += dr
                    cc += dc
                if cnt > best:
                    best = cnt
    return best


def has_your_win(board: np.ndarray) -> bool:
    """Return True if there is a line of ≥5 consecutive 1s."""
    # Quick scan for any run of 5+ 1s
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                continue
            # horizontal
            run = 1
            cc = c + 1
            while cc < 6 and board[r, cc] == 1:
                run += 1
                if run >= 5:
                    return True
                cc += 1
            # vertical
            run = 1
            rr = r + 1
            while rr < 6 and board[rr, c] == 1:
                run += 1
                if run >= 5:
                    return True
                rr += 1
            # diag \
            run = 1
            rr, cc = r + 1, c + 1
            while 0 <= rr < 6 and 0 <= cc < 6 and board[rr, cc] == 1:
                run += 1
                if run >= 5:
                    return True
                rr += 1
                cc += 1
            # diag /
            run = 1
            rr, cc = r + 1, c - 1
            while 0 <= rr < 6 and 0 <= cc < 6 and board[rr, cc] == 1:
                run += 1
                if run >= 5:
                    return True
                rr += 1
                cc -= 1
    return False


def rotate_quadrant(you: np.ndarray, opp: np.ndarray, quad: int, dir: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Rotate the specified 3×3 quadrant by 90° anticlockwise (L) or clockwise (R).
    The rotation affects both you and opponent marbles equally.
    """
    # Sub‑matrix coordinates
    start = {
        0: (0, 0),
        1: (0, 3),
        2: (3, 0),
        3: (3, 3),
    }[quad]
    r0, c0 = start
    # Preserve original board while applying rotation
    new_you = you.copy()
    new_opp = opp.copy()
    sub_you = new_you[r0:r0+3, c0:c0+3]
    sub_opp = new_opp[r0:r0+3, c0:c0+3]

    if dir == 'L':
        new_you[r0:r0+3, c0:c0+3] = np.rot90(sub_you, k=1)
        new_opp[r0:r0+3, c0:c0+3] = np.rot90(sub_opp, k=1)
    elif dir == 'R':
        new_you[r0:r0+3, c0:c0+3] = np.rot90(sub_you, k=-1)
        new_opp[r0:r0+3, c0:c0+3] = np.rot90(sub_opp, k=-1)
    else:
        raise ValueError("Direction must be 'L' or 'R'")
    return new_you, new_opp


def evaluate_move(you: np.ndarray, opp: np.ndarray, r: int, c: int,
                  quad: int, dir: str) -> float:
    """
    After placing a marble at (r,c) and rotating quadrant `quad` in direction `dir`,
    compute a score that captures immediate win, relative line lengths and board‑center bias.
    """
    # Immediate win check
    win_you = has_your_win(you)
    win_opp = has_your_win(opp)
    if win_you and not win_opp:
        return 10000.0
    if not win_you and win_opp:
        return -10000.0
    if win_you and win_opp:  # draw, not preferred
        return 0.0

    # Compute longest line lengths after the move
    y_line = longest_consecutive(you)
    o_line = longest_consecutive(opp)

    raw_score = y_line - o_line

    # Center‑bias: distance from the inner 2×2 block (rows 3‑4, cols 3‑4 in 1‑index)
    # weight = 1 / (manhattan distance + 1)
    manh = math.inf
    for center_r, center_c in [(2, 2), (2, 3), (3, 2), (3, 3)]:
        d = abs(r - center_r) + abs(c - center_c)
        manh = min(manh, d)
    weight = 1.0 / (manh + 1) if manh < math.inf else 0.0
    return raw_score * weight


def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """Return the next legal move as a string ``\"row,col,quad,dir\"``."""
    # Convert to numpy arrays for easy slicing & copying
    you_np = np.array(you, dtype=int)
    opp_np = np.array(opponent, dtype=int)

    empties = find_empty_cells(you_np, opp_np)
    if not empties:  # should not happen according to the spec, fallback to first empty-like cell
        empties = [(i, j) for i in range(6) for j in range(6) if you_np[i, j] == 0 and opp_np[i, j] == 0]

    best_score = -float('inf')
    best_move = None

    for r, c in empties:
        for quad in range(4):
            for dir in ('L', 'R'):
                # Apply move: place then rotate
                y_copy = you_np.copy()
                o_copy = opp_np.copy()
                y_copy[r, c] = 1   # you place a marble
                # Rotate (note: rotation includes the newly placed marble)
                y_rot, o_rot = rotate_quadrant(y_copy, o_copy, quad, dir)

                # Compute score
                score = evaluate_move(y_rot, o_rot, r, c, quad, dir)

                # Update best move (break ties by choosing a move that also wins if possible)
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, dir)
                elif abs(score - best_score) < 1e-6:
                    # Use a deterministic tie‑breaker: prefer central placements first,
                    # then a clockwise rotation (R) over anticlockwise (L) when scores equal.
                    current_man = math.inf
                    for center in [(2,2),(2,3),(3,2),(3,3)]:
                        current_man = min(current_man, abs(r-center[0])+abs(c-center[1]))
                    best_man = math.inf
                    for center in [(2,2),(2,3),(3,2),(3,3)]:
                        best_man = min(best_man, abs(best_move[0]-center[0])+abs(best_move[1]-center[1]))
                    if current_man < best_man:
                        best_move = (r, c, quad, dir)
                    elif current_man == best_man:
                        # Prefer R over L when weight is identical
                        if dir == 'R':
                            best_move = (r, c, quad, dir)

    # Convert 0‑based indices to 1‑based for the required output format
    row, col, quad, dir = best_move
    return f"{row+1},{col+1},{quad},{dir}"
