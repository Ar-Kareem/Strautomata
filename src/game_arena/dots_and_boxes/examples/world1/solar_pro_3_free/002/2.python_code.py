
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Choose the next move for Dots‑and‑Boxes on a 4x4 grid.
    Returns a string 'row,col,dir' where dir is 'H' or 'V'.
    """
    # pre‑compute per‑box statistics
    rows, cols = capture.shape  # capture is 4×4
    boxes_opp = np.zeros((rows, cols), dtype=int)
    boxes_my = np.zeros((rows, cols), dtype=int)

    for i in range(rows):
        for j in range(cols):
            top = horizontal[i, j]     # 0‑based edge index
            bottom = horizontal[i + 1, j]
            left = vertical[i, j]
            right = vertical[i, j + 1]

            opp = 0
            my = 0
            for e in (top, bottom, left, right):
                if e == -1:
                    opp += 1
                elif e == 1:
                    my += 1
            boxes_opp[i, j] = opp
            boxes_my[i, j] = my

    # locate empty edges
    h_empty = np.argwhere(horizontal == 0)   # shape (n,2)
    v_empty = np.argwhere(vertical == 0)

    # collect all candidate moves
    candidates = []
    # evaluate horizontal edges
    for r, c in h_empty:
        boxes = []
        if r > 0:
            boxes.append((r - 1, c))   # box above
        if r < rows - 1:
            boxes.append((r, c))       # box below

        safe = True
        capture_possible = False
        total_my = 0
        total_opp = 0
        for box in boxes:
            opp_val = boxes_opp[box]
            my_val = boxes_my[box]

            total_opp += opp_val
            total_my += my_val

            # unsafe if opponent already has 2 sides
            if opp_val >= 2:
                safe = False
                break
            # unsafe if opponent has 1 side and we already have 1 side in that box
            if opp_val == 1 and my_val == 1:
                safe = False
                break

        # after our move we would have one more of our side in each affected box
        # capture is possible if the box currently has exactly 3 drawn sides
        if safe:
            # capture check
            capture_possible = any(boxes_opp[b] + boxes_my[b] == 3 for b in boxes)

        score = 0
        if safe:
            score += 10                     # safe bonus
        if capture_possible:
            score += 100                    # capture bonus
        score += total_my                   # chain building (our already drawn sides)
        score -= total_opp                  # discourage edges that sit next to opponent sides
        candidates.append((score, r, c, 'H'))

    # evaluate vertical edges
    for r, c in v_empty:
        boxes = []
        if c > 0:
            boxes.append((r, c - 1))      # box on the left
        if c < cols - 1:
            boxes.append((r, c))          # box on the right

        safe = True
        capture_possible = False
        total_my = 0
        total_opp = 0
        for box in boxes:
            opp_val = boxes_opp[box]
            my_val = boxes_my[box]

            total_opp += opp_val
            total_my += my_val

            if opp_val >= 2:
                safe = False
                break
            if opp_val == 1 and my_val == 1:
                safe = False
                break

        if safe:
            capture_possible = any(boxes_opp[b] + boxes_my[b] == 3 for b in boxes)

        score = 0
        if safe:
            score += 10
        if capture_possible:
            score += 100
        score += total_my
        score -= total_opp
        candidates.append((score, r, c, 'V'))

    # pick the best move (max score, then smallest coordinates, H before V)
    if not candidates:
        raise RuntimeError("No legal move found – something went wrong")

    best = max(candidates, key=lambda cand: (cand[0], cand[1], cand[2], cand[3]))
    score, row, col, dir_char = best

    return f"{row},{col},{dir_char}"
