
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart policy for 4x4 Dots and Boxes (5x5 edge arrays).
    Returns a legal move string "row,col,dir" where dir is 'H' or 'V'.
    Strategy:
      - If any move completes boxes, pick the move completing the most.
      - Otherwise avoid moves that create any new 3-sided boxes.
      - If all moves create 3-sided boxes, pick one that minimizes that damage.
    """
    h = np.array(horizontal)  # copy-ish (we won't mutate originals)
    v = np.array(vertical)
    cap = np.array(capture)

    rows, cols = h.shape  # expected 5x5
    # number of boxes in each dimension
    box_rows = rows - 1
    box_cols = cols - 1

    # helper: count drawn edges around a given box (i,j) where 0 <= i < box_rows, 0 <= j < box_cols
    def edges_around_box(i, j, hh, vv):
        count = 0
        # top: horizontal[i, j]
        if hh[i, j] != 0:
            count += 1
        # bottom: horizontal[i+1, j]
        if hh[i+1, j] != 0:
            count += 1
        # left: vertical[i, j]
        if vv[i, j] != 0:
            count += 1
        # right: vertical[i, j+1]
        if vv[i, j+1] != 0:
            count += 1
        return count

    # helper: get adjacent boxes (list of (i,j)) for a horizontal edge (r,c)
    def adj_boxes_for_horizontal(r, c):
        boxes = []
        # top box at (r-1, c)
        if 0 <= r-1 < box_rows and 0 <= c < box_cols:
            boxes.append((r-1, c))
        # bottom box at (r, c)
        if 0 <= r < box_rows and 0 <= c < box_cols:
            boxes.append((r, c))
        return boxes

    # helper: adjacent boxes for a vertical edge (r,c)
    def adj_boxes_for_vertical(r, c):
        boxes = []
        # left box at (r, c-1)
        if 0 <= r < box_rows and 0 <= c-1 < box_cols:
            boxes.append((r, c-1))
        # right box at (r, c)
        if 0 <= r < box_rows and 0 <= c < box_cols:
            boxes.append((r, c))
        return boxes

    legal_moves = []

    # gather legal horizontal moves
    for r in range(rows):
        for c in range(cols):
            if h[r, c] == 0:
                legal_moves.append((r, c, 'H'))

    # gather legal vertical moves
    for r in range(rows):
        for c in range(cols):
            if v[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # If no legal moves (should be game over), return a fallback legal-ish string.
    if not legal_moves:
        return "0,0,H"

    best_capture_moves = []
    best_capture_count = -1

    safe_moves = []  # moves that create zero new 3-sided boxes
    unsafe_moves = []  # moves that create >0 new 3-sided boxes

    # Evaluate each move by simulation (without changing originals)
    for move in legal_moves:
        r, c, d = move
        # copy arrays to simulate
        hh = h.copy()
        vv = v.copy()
        # mark the edge as drawn by us
        if d == 'H':
            hh[r, c] = 1
            adj_boxes = adj_boxes_for_horizontal(r, c)
        else:
            vv[r, c] = 1
            adj_boxes = adj_boxes_for_vertical(r, c)

        # count how many boxes would be captured by this move (boxes that become 4 edges and unclaimed before)
        captures = 0
        for (i, j) in adj_boxes:
            if 0 <= i < box_rows and 0 <= j < box_cols:
                before_edges = edges_around_box(i, j, h, v)
                after_edges = edges_around_box(i, j, hh, vv)
                if cap[i, j] == 0 and after_edges == 4 and before_edges < 4:
                    captures += 1

        # count newly created 3-sided boxes (boxes that become exactly 3 edges after this move and were not 3 before)
        new_threes = 0
        # Also compute an "exposure" score: sum of after_edges for adjacent boxes (lower is better)
        exposure = 0
        for (i, j) in adj_boxes:
            if 0 <= i < box_rows and 0 <= j < box_cols:
                before_edges = edges_around_box(i, j, h, v)
                after_edges = edges_around_box(i, j, hh, vv)
                exposure += after_edges
                if cap[i, j] == 0 and after_edges == 3 and before_edges != 3:
                    new_threes += 1

        # Prioritize capture moves
        if captures > 0:
            if captures > best_capture_count:
                best_capture_count = captures
                best_capture_moves = [(move, new_threes, exposure)]
            elif captures == best_capture_count:
                best_capture_moves.append((move, new_threes, exposure))
        else:
            # non-capturing move
            if new_threes == 0:
                safe_moves.append((move, new_threes, exposure))
            else:
                unsafe_moves.append((move, new_threes, exposure))

    # If there are capturing moves, pick the best among them:
    if best_capture_moves:
        # prefer captures that create fewer new 3-sided boxes, then lower exposure, then lexicographic coords
        best_capture_moves.sort(key=lambda x: (x[1], x[2], x[0][0], x[0][1], x[0][2]))
        chosen = best_capture_moves[0][0]
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # If safe moves exist, pick one minimizing exposure then coordinates
    if safe_moves:
        safe_moves.sort(key=lambda x: (x[2], x[0][0], x[0][1], x[0][2]))
        chosen = safe_moves[0][0]
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # Otherwise all moves are unsafe; pick moves minimizing new_threes, then exposure
    unsafe_moves.sort(key=lambda x: (x[1], x[2], x[0][0], x[0][1], x[0][2]))
    chosen = unsafe_moves[0][0]
    return f"{chosen[0]},{chosen[1]},{chosen[2]}"
