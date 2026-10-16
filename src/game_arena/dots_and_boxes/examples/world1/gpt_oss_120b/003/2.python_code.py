
import numpy as np
from typing import List, Tuple

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def box_side_count(i: int, j: int,
                   h: np.ndarray, v: np.ndarray) -> int:
    """
    Returns the number of drawn sides around the box (i, j)
    (0 <= i, j < 4).
    """
    cnt = 0
    if h[i, j] != 0:       cnt += 1  # top
    if h[i + 1, j] != 0:   cnt += 1  # bottom
    if v[i, j] != 0:       cnt += 1  # left
    if v[i, j + 1] != 0:   cnt += 1  # right
    return cnt


def affected_boxes(edge: Tuple[int, int, str]) -> List[Tuple[int, int]]:
    """
    For a given edge returns the list of boxes (i, j) that touch it.
    Edge is (row, col, dir) where dir is 'H' or 'V'.
    """
    r, c, d = edge
    boxes = []
    if d == 'H':
        if r > 0:
            boxes.append((r - 1, c))
        if r < 4:
            boxes.append((r, c))
    else:  # 'V'
        if c > 0:
            boxes.append((r, c - 1))
        if c < 4:
            boxes.append((r, c))
    return boxes


def evaluate_move(edge: Tuple[int, int, str],
                  h: np.ndarray, v: np.ndarray) -> Tuple[int, int]:
    """
    Simulate drawing the given edge and return:
        (completed, dangerous)
    completed – how many boxes become 4‑sided (i.e. we capture now)
    dangerous – how many boxes become 3‑sided (i.e. give opponent a free capture)
    """
    r, c, d = edge
    # copy counts locally (no need to copy whole arrays)
    completed = 0
    dangerous = 0
    for (i, j) in affected_boxes(edge):
        # current side count before the move
        sides_before = box_side_count(i, j, h, v)
        # after drawing this edge the count increases by 1
        sides_after = sides_before + 1
        if sides_after == 4:
            completed += 1
        elif sides_after == 3:
            dangerous += 1
    return completed, dangerous


def list_legal_moves(h: np.ndarray, v: np.ndarray) -> List[Tuple[int, int, str]]:
    """
    Returns all legal edges on a 4x4 board.
    Horizontal: rows 0‑4, cols 0‑3
    Vertical:   rows 0‑3, cols 0‑4
    """
    moves = []
    # horizontal
    for r in range(5):
        for c in range(4):
            if h[r, c] == 0:
                moves.append((r, c, 'H'))
    # vertical
    for r in range(4):
        for c in range(5):
            if v[r, c] == 0:
                moves.append((r, c, 'V'))
    return moves


# ------------------------------------------------------------
# Main policy function
# ------------------------------------------------------------

def policy(horizontal: np.ndarray,
           vertical: np.ndarray,
           capture: np.ndarray) -> str:
    """
    Choose a legal move for the current player.
    Returns a string ",dir".
    """
    # Gather all legal moves
    legal_moves = list_legal_moves(horizontal, vertical)

    if not legal_moves:
        # Board full – should never be called, but return a dummy move.
        return "0,0,H"

    # 1. Look for capturing moves
    best_capture = -1
    best_move_capture = None
    for move in legal_moves:
        completed, _ = evaluate_move(move, horizontal, vertical)
        if completed > 0:
            if completed > best_capture:
                best_capture = completed
                best_move_capture = move
                # maximum possible is 2; break early
                if best_capture == 2:
                    break
    if best_move_capture is not None:
        r, c, d = best_move_capture
        return f"{r},{c},{d}"

    # 2. Safe moves (do not create a 3‑sided box)
    safe_moves = []
    for move in legal_moves:
        _, dangerous = evaluate_move(move, horizontal, vertical)
        if dangerous == 0:
            safe_moves.append(move)

    if safe_moves:
        r, c, d = safe_moves[0]   # deterministic first safe move
        return f"{r},{c},{d}"

    # 3. All moves are dangerous – pick the one that creates the fewest 3‑sided boxes
    min_danger = 10
    best_move_danger = None
    for move in legal_moves:
        _, dangerous = evaluate_move(move, horizontal, vertical)
        if dangerous < min_danger:
            min_danger = dangerous
            best_move_danger = move
            if min_danger == 0:
                break
    # best_move_danger must be set (there is at least one move)
    r, c, d = best_move_danger
    return f"{r},{c},{d}"
