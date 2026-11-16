
import numpy as np
from typing import List, Tuple

# directions for 5‑in‑a‑row windows
DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]

def rotate_quadrant(arr: np.ndarray, quad: int, left: bool) -> None:
    """Rotate the 3×3 quadrant *in place*."""
    rows = slice(0, 3) if quad < 2 else slice(3, 6)
    cols = slice(0, 3) if quad % 2 == 0 else slice(3, 6)
    sub = arr[rows, cols]
    k = 1 if left else -1  # np.rot90 with k>0 rotates anticlockwise
    arr[rows, cols] = np.rot90(sub, k=k)

def check_five(board: np.ndarray) -> bool:
    """Return True if board has any 5‑in‑a‑row of 1s."""
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                continue
            for dr, dc in DIRS:
                rr, cc = r + 4 * dr, c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    ok = True
                    for i in range(5):
                        if board[r + i * dr, c + i * dc] == 0:
                            ok = False
                            break
                    if ok:
                        return True
    return False

def line_score(me: np.ndarray, opp: np.ndarray) -> int:
    """Heuristic: sum k^2 for each 5‑cell window that contains only my stones or empties."""
    score = 0
    for dr, dc in DIRS:
        for r in range(6):
            for c in range(6):
                rr, cc = r + 4 * dr, c + 4 * dc
                if not (0 <= rr < 6 and 0 <= cc < 6):
                    continue
                # collect the 5 cells
                my_cnt = 0
                blocked = False
                for i in range(5):
                    cell_r = r + i * dr
                    cell_c = c + i * dc
                    if opp[cell_r, cell_c]:
                        blocked = True
                        break
                    if me[cell_r, cell_c]:
                        my_cnt += 1
                if not blocked:
                    score += my_cnt * my_cnt
    return score

def evaluate(me: np.ndarray, opp: np.ndarray) -> int:
    """Combined heuristic score."""
    return line_score(me, opp) - line_score(opp, me)

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    you_arr = np.array(you, dtype=np.int8)
    opp_arr = np.array(opponent, dtype=np.int8)

    empties: List[Tuple[int, int]] = [(r, c)
                                     for r in range(6)
                                     for c in range(6)
                                     if you_arr[r, c] == 0 and opp_arr[r, c] == 0]

    best_move = None
    best_score = -10**9

    for r, c in empties:
        for quad in range(4):
            for dir_char, left in (('L', True), ('R', False)):
                # copy boards
                my = you_arr.copy()
                op = opp_arr.copy()
                # place marble
                my[r, c] = 1
                # rotate quadrant
                rotate_quadrant(my, quad, left)
                rotate_quadrant(op, quad, left)

                my_win = check_five(my)
                opp_win = check_five(op)

                # immediate winning move – take it
                if my_win and not opp_win:
                    return f"{r+1},{c+1},{quad},{dir_char}"

                # score the position
                score = (1000 if my_win else 0) - (1000 if opp_win else 0)
                score += evaluate(my, op)

                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, dir_char)

    # there is always at least one legal move
    r, c, quad, dir_char = best_move
    return f"{r+1},{c+1},{quad},{dir_char}"
