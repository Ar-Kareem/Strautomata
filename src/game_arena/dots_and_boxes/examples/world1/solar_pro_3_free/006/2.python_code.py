
import numpy as np

def evaluate_move(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
    row: int,
    col: int,
    dir: str,
) -> tuple[int, int]:
    """
    Simulate drawing the given edge and return:
        - number of opponent boxes captured (1 per completed box where we do not own any edge)
        - number of our boxes captured (1 per completed box where at least one edge is ours)
    """
    h = horizontal.copy()
    v = vertical.copy()
    c = capture.copy()

    if dir == "H":
        h[row, col] = 1  # our draw
    else:  # dir == "V"
        v[row, col] = 1

    opponent_boxes = 0
    self_boxes = 0

    # each of the 4×4 boxes is defined by its four edges
    for r in range(4):
        for c in range(4):
            total = (
                h[r, c] + h[r, c + 1] + v[r, c] + v[r, c + 1]
            )  # sum of edge values (0 = none, 1 = us, -1 = opponent)

            if total == 4:  # box becomes completed
                # if any of the four edges belongs to us, we claim it
                if any(
                    h[r, c] == 1,
                    h[r, c + 1] == 1,
                    v[r, c] == 1,
                    v[r, c + 1] == 1,
                ):
                    c[r, c] = 1
                    self_boxes += 1
                else:
                    c[r, c] = -1
                    opponent_boxes += 1

    return opponent_boxes, self_boxes


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Choose the next move for Dots‑and‑Boxes on a 4×4 grid.
    Returns a string 'row,col,dir' where dir is either 'H' or 'V'.
    """
    # Count boxes already owned
    our_boxes = np.sum(capture == 1)
    opp_boxes = np.sum(capture == -1)

    # Gather all legal moves
    candidates = []

    # Horizontal edges
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                opp, own = evaluate_move(
                    horizontal, vertical, capture, r, c, "H"
                )
                candidates.append((opp, own, r, c, "H"))

    # Vertical edges
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                opp, own = evaluate_move(
                    horizontal, vertical, capture, r, c, "V"
                )
                candidates.append((opp, own, r, c, "V"))

    # Heuristic ordering
    if our_boxes > opp_boxes:
        # Prefer safe moves (0 opponent boxes). If several, choose the one with the fewest of our own boxes.
        safe = [m for m in candidates if m[0] == 0]
        if safe:
            safe.sort(key=lambda x: (x[1], x[2], x[3]))  # own boxes asc, then row, col
            best = safe[0]
        else:
            # If every safe move captures at least one box, pick the one with the smallest opponent impact.
            candidates.sort(key=lambda x: (x[0], x[1]))
            best = candidates[0]
    else:
        # We are behind or tied – try to capture a box while hurting the opponent as little as possible.
        giving = [m for m in candidates if m[1] > 0]
        if giving:
            giving.sort(key=lambda x: (x[0], x[1]))  # opponent boxes asc, then ours
            best = giving[0]
        else:
            # No giveaway move; fall back to the safest available edge.
            candidates.sort(key=lambda x: (x[0], x[1]))
            best = candidates[0]

    # Build the move string
    row, col, dir = best[2], best[3], best[4]
    return f"{row},{col},{dir}"
