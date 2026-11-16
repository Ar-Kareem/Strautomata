
import numpy as np
from typing import Tuple, List

def _box_side_count(r: int, c: int,
                    horiz: np.ndarray, vert: np.ndarray) -> int:
    """Number of already drawn edges around the box (r,c)."""
    cnt = 0
    # top
    cnt += int(horiz[r, c] != 0)
    # bottom
    cnt += int(horiz[r + 1, c] != 0)
    # left
    cnt += int(vert[r, c] != 0)
    # right
    cnt += int(vert[r, c + 1] != 0)
    return cnt


def policy(horizontal: np.ndarray, vertical: np.ndarray,
           capture: np.ndarray) -> str:
    """
    Return a legal move for the 4×4 Dots‑and‑Boxes board.

    Move format: "row,col,dir" where dir is 'H' or 'V'.
    """
    best_move = None
    best_gain = -1          # number of boxes we would capture
    best_danger = 10**9      # number of new 3‑side boxes we would create

    # ------------------------------------------------------------------
    # helper to evaluate a candidate edge
    # ------------------------------------------------------------------
    def evaluate(row: int, col: int, is_h: bool) -> Tuple[int, int]:
        """Return (gain, danger) for the edge."""
        gain = 0
        danger = 0

        # boxes that share this edge
        boxes: List[Tuple[int, int]] = []

        if is_h:
            # top box (if any)
            if row < 4:
                boxes.append((row, col))
            # bottom box
            if row > 0:
                boxes.append((row - 1, col))
        else:  # vertical
            # left box
            if col < 4:
                boxes.append((row, col))
            # right box
            if col > 0:
                boxes.append((row, col - 1))

        for (br, bc) in boxes:
            cur = _box_side_count(br, bc, horizontal, vertical)
            if cur == 3:          # this edge would complete the box
                gain += 1
            elif cur == 2:        # after playing we would have 3 sides → danger
                danger += 1

        return gain, danger

    # ------------------------------------------------------------------
    # enumerate all legal moves
    # ------------------------------------------------------------------
    for r in range(5):
        for c in range(5):
            # horizontal edges exist only for c < 4
            if c < 4 and horizontal[r, c] == 0:
                g, d = evaluate(r, c, True)
                if g > best_gain or (g == best_gain and d < best_danger):
                    best_gain, best_danger = g, d
                    best_move = (r, c, 'H')
            # vertical edges exist only for r < 4
            if r < 4 and vertical[r, c] == 0:
                g, d = evaluate(r, c, False)
                if g > best_gain or (g == best_gain and d < best_danger):
                    best_gain, best_danger = g, d
                    best_move = (r, c, 'V')

    # ------------------------------------------------------------------
    # Fallback (should never happen)
    # ------------------------------------------------------------------
    if best_move is None:
        # find any empty edge
        for r in range(5):
            for c in range(5):
                if c < 4 and horizontal[r, c] == 0:
                    return f"{r},{c},H"
                if r < 4 and vertical[r, c] == 0:
                    return f"{r},{c},V"
        # board full – return dummy
        return "0,0,H"

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
