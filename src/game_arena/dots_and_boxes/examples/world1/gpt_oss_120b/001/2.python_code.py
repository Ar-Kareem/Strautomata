
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Return a legal move for Dots and Boxes on a 4x4 board.

    Parameters
    ----------
    horizontal : np.ndarray, shape (5,5)
        0 = empty, non‑zero = already drawn.
    vertical : np.ndarray, shape (5,5)
        Same as horizontal but for vertical edges.
    capture : np.ndarray, shape (5,5)
        Ownership of boxes (unused by the policy).

    Returns
    -------
    move : str
        "row,col,dir" with dir in {'H','V'}.
    """

    # ---- helper functions -------------------------------------------------
    def box_sides_filled(i: int, j: int) -> int:
        """Number of drawn edges around box (i,j)."""
        # top, bottom, left, right
        count = 0
        if horizontal[i, j] != 0:
            count += 1
        if horizontal[i + 1, j] != 0:
            count += 1
        if vertical[i, j] != 0:
            count += 1
        if vertical[i, j + 1] != 0:
            count += 1
        return count

    def adjacent_boxes(move):
        """Return list of (i,j) box coordinates adjacent to the edge."""
        r, c, d = move
        if d == 'H':
            boxes = []
            if r > 0:
                boxes.append((r - 1, c))
            if r < 4:
                boxes.append((r, c))
            return boxes
        else:  # 'V'
            boxes = []
            if c > 0:
                boxes.append((r, c - 1))
            if c < 4:
                boxes.append((r, c))
            return boxes

    # ---- gather all legal moves -------------------------------------------
    moves = []                     # (row, col, dir)
    for r in range(horizontal.shape[0]):
        for c in range(horizontal.shape[1]):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    for r in range(vertical.shape[0]):
        for c in range(vertical.shape[1]):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))

    if not moves:
        # Should never happen; return a dummy legal-looking move.
        return "0,0,H"

    # ---- 1) look for box‑completing moves ---------------------------------
    best_complete = []
    max_boxes = 0
    for mv in moves:
        completed = 0
        for (i, j) in adjacent_boxes(mv):
            if box_sides_filled(i, j) == 3:  # edge would close this box
                completed += 1
        if completed > max_boxes:
            max_boxes = completed
            best_complete = [mv]
        elif completed == max_boxes and completed > 0:
            best_complete.append(mv)

    if max_boxes > 0:
        # Prefer a move that completes two boxes (double) if such exists.
        chosen = best_complete[0]
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # ---- 2) safe moves (do not create a 3‑sided box) -----------------------
    safe_moves = []
    for mv in moves:
        creates_three = False
        for (i, j) in adjacent_boxes(mv):
            if box_sides_filled(i, j) == 2:  # after playing we would have 3
                creates_three = True
                break
        if not creates_three:
            safe_moves.append(mv)

    if safe_moves:
        chosen = safe_moves[0]
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # ---- 3) all remaining moves are dangerous; minimize damage ------------
    # count how many adjacent boxes would become three‑sided
    min_three = 10
    candidates = []
    for mv in moves:
        three_cnt = 0
        for (i, j) in adjacent_boxes(mv):
            if box_sides_filled(i, j) == 2:
                three_cnt += 1
        if three_cnt < min_three:
            min_three = three_cnt
            candidates = [mv]
        elif three_cnt == min_three:
            candidates.append(mv)

    chosen = candidates[0]
    return f"{chosen[0]},{chosen[1]},{chosen[2]}"
