
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Dimensions of the grid (5x5 for edges, 4x4 for boxes)
    n = 4  # number of boxes per row/col

    def is_legal(row, col, d):
        if d == 'H':
            return 0 <= row <= 4 and 0 <= col <= 3 and horizontal[row, col] == 0
        elif d == 'V':
            return 0 <= row <= 3 and 0 <= col <= 4 and vertical[row, col] == 0
        return False

    def count_box_edges(r, c, h, v):
        # Count how many of the 4 edges around box (r,c) are filled
        edges = 0
        edges += 1 if h[r, c] != 0 else 0        # top
        edges += 1 if h[r+1, c] != 0 else 0      # bottom
        edges += 1 if v[r, c] != 0 else 0        # left
        edges += 1 if v[r, c+1] != 0 else 0      # right
        return edges

    def completes_box(row, col, dir, h, v):
        count = 0
        if dir == 'H':
            c = col
            r1, r2 = row-1, row  # above and below
            if r1 >= 0 and count_box_edges(r1, c, h, v) == 3:
                # We just added the bottom edge to box (r1, c)
                temp_h = h.copy()
                temp_h[row, col] = 1
                if count_box_edges(r1, c, temp_h, v) == 4:
                    count +=  Newton
            if r2 < n and count_box_edges(r2, c, h, v) == 3:
                temp_h = h.copy()
                temp_h[row, col] = 1
                if count_box_edges(r2, c, temp_h, v) == 4:
                    count += 1
        else:  # 'V'
            r = row
            c1, c2 = col-1, col  # left and right
            if c1 >= 0 and count_box_edges(r, c1, h, v) == 3:
                temp_v = v.copy()
                temp_v[row, col] = 1
                if count_box_edges(r, c1, h, temp_v) == 4:
                    count += 1
            if c2 < n and count_box_edges(r, c2, h, v) == 3:
                temp_v = v.copy()
                temp_v[row, col] = 1
                if count_box_edges(r, c2, h, temp_v) == 4:
                    count += 1
        return count

    def score_move(row, col, dir):
        # Simulate move and score it
        additional_boxes = completes_box(row, col, dir, horizontal, vertical)
        if additional_boxes > 0:
            # Highly prefer capturing boxes since we get another turn
            return 1000 + additional_boxes  # incentive for more than one box

        # If no capture, check how many boxes we are contributing to
        # and whether we create any box with 3 edges (dangerous)
        danger = 0
        benefit = 0

        if dir == 'H':
            # Affects boxes above (row-1, col) and below (row, col)
            for dr, dc in [(-1, 0), (0, 0)]:
                r, c = row + dr, col
                if 0 <= r < n and 0 <= c < n:
                    edges_before = count_box_edges(r, c, horizontal, vertical)
                    edges_after = edges_before + 1
                    if edges_after == 3:
                        danger += 1  # now has 3 edges, opponent can take it
                    elif edges_after == 2:
                        benefit += 0.5  # progressing safely
        else:  # 'V'
            # Affects boxes to the left (row, col-1) and right (row, col)
            for dr, dc in [(0, -1), (0, 0)]:
                r, c = row, col + dc
                if 0 <= r < n and 0 <= c < n:
                    edges_before = count_box_edges(r, c, horizontal, vertical)
                    edges_after = edges_before + 1
                    if edges_after == 3:
                        danger += 1
                    elif edges_after == 2:
                        benefit += 0.5

        # Score: benefit minus danger
        return 10 + benefit - 10 * danger

    # Collect all legal moves
    moves = []
    for r in range(5):
        for c in range(4):
            if is_legal(r, c, 'H'):
                moves.append((r, c, 'H'))
        for c in range(5):
            if is_legal(r, c, 'V'):
                moves.append((r, c, 'V'))

    if not moves:
        # This should not happen in a real game, but fallback
        return "0,0,H"

    # Score each move
    scored_moves = []
    for r, c, d in moves:
        score = score_move(r, c, d)
        scored_moves.append((score, r, c, d))

    # Choose the move with the highest score
    # Break ties by row-major order to ensure determinism
    best = max(scored_moves, key=lambda x: (x[0], -x[1], -x[2]))  # prefer higher score, then earlier row/col
    _, best_row, best_col, best_dir = best

    return f"{best_row},{best_col},{best_dir}"
