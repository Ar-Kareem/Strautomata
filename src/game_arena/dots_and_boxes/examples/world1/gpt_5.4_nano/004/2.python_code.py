
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Board is 4x4 boxes => edges are 5x5 in each orientation.
    # horizontal[r,c] is the edge between boxes (r-1,c) and (r,c) for 0<=r<=4, 0<=c<=4,
    # but for counting box sides we only use the conventions:
    # A box at (br,bc) has:
    #   top    = horizontal[br, bc]
    #   bottom = horizontal[br+1, bc]
    #   left   = vertical[br, bc]
    #   right  = vertical[br, bc+1]
    H = horizontal
    V = vertical

    # Helper: compute how many sides are filled for a given box
    def box_sides_filled(br, bc):
        return (
            (H[br, bc] != 0) +
            (H[br+1, bc] != 0) +
            (V[br, bc] != 0) +
            (V[br, bc+1] != 0)
        )

    # Helper: check whether a specific move would complete any box(es).
    # Returns (captures_count, completed_boxes_count, completed_positions)
    def move_effect(row, col, dirc):
        completed = []
        if dirc == 'H':
            # Drawing horizontal[row,col] affects boxes with top=row or bottom=row
            # It is top for box row-? Actually:
            # box(br, bc) uses horizontal[br, bc] as top.
            # So horizontal[row,col] is top of box (row, col) if row in 0..3 and col in 0..3
            if 0 <= row <= 3 and 0 <= col <= 3:
                br, bc = row, col
                # If we draw this edge, it increases top from filled to filled
                # Completed if box would reach 4.
                sides_now = box_sides_filled(br, bc)
                # But horizontal[row,col] might already be filled (caller ensures it's empty)
                # So after drawing, sides_now becomes sides_now+1
                if sides_now == 3:
                    completed.append((br, bc))
            # It is bottom of box (row-1, col)
            if 1 <= row <= 4 and 0 <= col <= 3:
                br, bc = row-1, col
                sides_now = box_sides_filled(br, bc)
                if sides_now == 3:
                    completed.append((br, bc))
        else:  # dirc == 'V'
            # vertical[row,col] affects boxes:
            # It is left for box (row, col) if row in 0..3 and col in 0..3
            if 0 <= row <= 3 and 0 <= col <= 3:
                br, bc = row, col
                sides_now = box_sides_filled(br, bc)
                if sides_now == 3:
                    completed.append((br, bc))
            # It is right for box (row, col-1) if row in 0..3 and 1<=col<=4
            if 0 <= row <= 3 and 1 <= col <= 4:
                br, bc = row, col-1
                sides_now = box_sides_filled(br, bc)
                if sides_now == 3:
                    completed.append((br, bc))
        # completed may have duplicates in weird cases (not here), dedupe
        if completed:
            completed = list(set(completed))
        return completed

    # Helper: would this move create a box with exactly 3 sides after playing?
    # (i.e., a box that is currently 2-sided and this move is the third).
    def move_creates_three_sided(row, col, dirc):
        three_count = 0
        if dirc == 'H':
            candidates = []
            if 0 <= row <= 3 and 0 <= col <= 3:
                candidates.append((row, col))
            if 1 <= row <= 4 and 0 <= col <= 3:
                candidates.append((row-1, col))
        else:
            candidates = []
            if 0 <= row <= 3 and 0 <= col <= 3:
                candidates.append((row, col))
            if 0 <= row <= 3 and 1 <= col <= 4:
                candidates.append((row, col-1))

        for br, bc in candidates:
            sides_now = box_sides_filled(br, bc)
            # since move edge is empty, drawing it increases sides by 1
            if sides_now == 2:
                three_count += 1
        return three_count

    # Build list of all legal moves
    moves = []
    # horizontal edges: row 0..4, col 0..4
    for r in range(5):
        for c in range(5):
            if H[r, c] == 0:
                moves.append((r, c, 'H'))
    for r in range(5):
        for c in range(5):
            if V[r, c] == 0:
                moves.append((r, c, 'V'))

    # 1) Look for immediate captures
    best_capture_moves = []
    for r, c, d in moves:
        completed_boxes = move_effect(r, c, d)
        if completed_boxes:
            best_capture_moves.append((len(completed_boxes), r, c, d))

    if best_capture_moves:
        # Prefer max number of boxes captured
        best_capture_moves.sort(key=lambda x: (-x[0], x[1], x[2], x[3]))
        _, r, c, d = best_capture_moves[0]
        return f"{r},{c},{d}"

    # 2) Otherwise avoid creating 3-sided boxes (giveaway)
    scored = []
    for r, c, d in moves:
        three_ct = move_creates_three_sided(r, c, d)
        # Also consider centrality a bit (lower tie-break): prefer edges closer to center.
        # Box center is around (1.5..2.5); approximate using coordinates.
        # For H edges, use (r+0.0, c+0.5); for V, use (r+0.5, c+0.0)
        if d == 'H':
            x = c + 0.5
            y = r + 0.0
        else:
            x = c + 0.0
            y = r + 0.5
        center_dist = (x - 2.0) ** 2 + (y - 2.0) ** 2
        # Lower is better; primarily minimize three_ct
        scored.append((three_ct, center_dist, r, c, d))

    scored.sort(key=lambda t: (t[0], t[1], t[2], t[3], t[4]))
    # If multiple equally best, randomize among first few to reduce predictability
    best_three = scored[0][0]
    top = [t for t in scored if t[0] == best_three]
    # among those, take those with minimal center_dist
    min_center = min(t[1] for t in top)
    top2 = [t for t in top if t[1] == min_center]
    pick = random.choice(top2)
    _, _, r, c, d = pick
    return f"{r},{c},{d}"
