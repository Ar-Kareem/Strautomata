
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Choose a Dots-and-Boxes move on a 4x4 boxes board (arrays given).
    Returns a string "row,col,dir" where dir is 'H' or 'V'.
    """
    # Helper shapes
    h_shape = horizontal.shape
    v_shape = vertical.shape
    b_shape = capture.shape  # expected number of boxes (rows, cols)
    b_rows, b_cols = b_shape

    # Safe accessor for arrays: return 1 if index out of bounds (treat as filled),
    # 0/1 otherwise. Treating out-of-bounds as filled avoids counting non-existent edges.
    def h_val(r, c):
        if 0 <= r < h_shape[0] and 0 <= c < h_shape[1]:
            return int(horizontal[r, c] != 0)
        return 1

    def v_val(r, c):
        if 0 <= r < v_shape[0] and 0 <= c < v_shape[1]:
            return int(vertical[r, c] != 0)
        return 1

    # Count number of sides currently filled for a box at (br, bc)
    def box_sides(br, bc):
        # top: horizontal[br, bc]
        s = 0
        if 0 <= br < h_shape[0] and 0 <= bc < h_shape[1]:
            s += h_val(br, bc)
        if 0 <= br + 1 < h_shape[0] and 0 <= bc < h_shape[1]:
            s += h_val(br + 1, bc)
        if 0 <= br < v_shape[0] and 0 <= bc < v_shape[1]:
            s += v_val(br, bc)
        if 0 <= br < v_shape[0] and 0 <= bc + 1 < v_shape[1]:
            s += v_val(br, bc + 1)
        return s

    # Get adjacent boxes (list of (br,bc)) for a given edge
    def adjacent_boxes_for_H(r, c):
        # Horizontal edge at (r,c) touches boxes (r-1,c) (above) and (r,c) (below)
        res = []
        if 0 <= r - 1 < b_rows and 0 <= c < b_cols:
            res.append((r - 1, c))
        if 0 <= r < b_rows and 0 <= c < b_cols:
            res.append((r, c))
        return res

    def adjacent_boxes_for_V(r, c):
        # Vertical edge at (r,c) touches boxes (r,c-1) (left) and (r,c) (right)
        res = []
        if 0 <= r < b_rows and 0 <= c - 1 < b_cols:
            res.append((r, c - 1))
        if 0 <= r < b_rows and 0 <= c < b_cols:
            res.append((r, c))
        return res

    legal_moves = []

    # Collect legal horizontal moves
    for r in range(h_shape[0]):
        for c in range(h_shape[1]):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))

    # Collect legal vertical moves
    for r in range(v_shape[0]):
        for c in range(v_shape[1]):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # If no legal moves, return fallback (should not normally happen)
    if not legal_moves:
        return "0,0,H"

    # Evaluate each move for captures and safety
    evaluated = []
    for (r, c, d) in legal_moves:
        if d == 'H':
            adj_boxes = adjacent_boxes_for_H(r, c)
        else:
            adj_boxes = adjacent_boxes_for_V(r, c)

        # Count how many boxes would be completed (i.e., currently have 3 sides)
        captures = 0
        sides_after_sum = 0
        creates_three_count = 0
        max_sides_after = -1

        for (br, bc) in adj_boxes:
            before = box_sides(br, bc)
            after = before + 1  # playing this edge adds one side to adjacent boxes
            sides_after_sum += after
            if before == 3:
                captures += 1
            if after == 3:
                creates_three_count += 1
            if after > max_sides_after:
                max_sides_after = after

        # For boxes that are not adjacent, doesn't change
        # Key tuple for sorting:
        # Primary: prefer capturing moves (captures desc), then prefer safe moves (creates_three_count == 0),
        # then prefer fewer created 3-sided boxes, then smaller sides_after_sum, then lexicographic (r,c,d)
        evaluated.append({
            'move': (r, c, d),
            'captures': captures,
            'creates_three': creates_three_count,
            'sides_after_sum': sides_after_sum,
            'max_after': max_sides_after
        })

    # First, if any capturing moves exist, take one that captures the most boxes
    capturing_moves = [e for e in evaluated if e['captures'] > 0]
    if capturing_moves:
        # Choose maximum captures, then minimal sides_after_sum, then lexicographic
        capturing_moves.sort(key=lambda e: (-e['captures'], e['sides_after_sum'], e['move'][0], e['move'][1], e['move'][2]))
        chosen = capturing_moves[0]['move']
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # No immediate captures: look for safe moves (creates_three == 0)
    safe_moves = [e for e in evaluated if e['creates_three'] == 0]
    if safe_moves:
        # minimize sides_after_sum, then minimal max_after, then lexicographic
        safe_moves.sort(key=lambda e: (e['sides_after_sum'], e['max_after'], e['move'][0], e['move'][1], e['move'][2]))
        chosen = safe_moves[0]['move']
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # No safe moves: choose one that minimizes number of created 3-sided boxes,
    # then minimize sides_after_sum, then lexicographic
    evaluated.sort(key=lambda e: (e['creates_three'], e['sides_after_sum'], e['max_after'], e['move'][0], e['move'][1], e['move'][2]))
    chosen = evaluated[0]['move']
    return f"{chosen[0]},{chosen[1]},{chosen[2]}"
