
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Grid size: 5x5 edges for a 4x4 box grid
    n = 4  # number of boxes per side
    moves = []

    # Generate all legal moves
    for row in range(n + 1):
        for col in range(n + 1):
            # Horizontal edges: connect (row, col) -> (row, col+1), exist at [row, col] in horizontal
            if col < n and horizontal[row, col] == 0:
                moves.append((row, col, 'H'))
            # Vertical edges: connect (row, col) -> (row+1, col), exist at [row, col] in vertical
            if row < n and vertical[row, col] == 0:
                moves.append((row, col, 'V'))

    # Utility: simulate move and count captures
    def simulate_move(h, v, r, c, d):
        h_new = h.copy()
        v_new = v.copy()
        captures = 0
        boxes_completed = []

        if d == 'H':
            h_new[r, c] = 1
            # Check box above (r-1, c) and below (r, c)
            if r > 0 and h_new[r-1, c] != 0 and v_new[r-1, c] != 0 and v_new[r-1, c+1] != 0:
                boxes_completed.append((r-1, c))
            if r < n and h_new[r+1, c] != 0 and v_new[r, c] != 0 and v_new[r, c+1] != 0:
                boxes_completed.append((r, c))
        else:  # d == 'V'
            v_new[r, c] = 1
            # Check box to the left (r, c-1) and right (r, c)
            if c > 0 and v_new[r, c-1] != 0 and h_new[r, c-1] != 0 and h_new[r+1, c-1] != 0:
                boxes_completed.append((r, c-1))
            if c < n and v_new[r, c+1] != 0 and h_new[r, c] != 0 and h_new[r+1, c] != 0:
                boxes_completed.append((r, c))
        return len(boxes_completed), boxes_completed

    # First: look for moves that capture at least one box (safe greedy capture)
    capturing_moves = []
    for (r, c, d) in moves:
        capt, _ = simulate_move(horizontal, vertical, r, c, d)
        if capt > 0:
            capturing_moves.append((r, c, d, capt))

    if capturing_moves:
        # Prefer moves with more captures (e.g. double capture)
        capturing_moves.sort(key=lambda x: x[3], reverse=True)
        r, c, d, _ = capturing_moves[0]
        return f"{r},{c},{d}"

    # Second: avoid moves that create a box with 3 sides
    safe_moves = []
    for (r, c, d) in moves:
        # Simulate temporarily
        h_temp = horizontal.copy()
        v_temp = vertical.copy()
        if d == 'H':
            h_temp[r, c] = 1
        else:
            v_temp[r, c] = 1

        # After the move, check how many boxes go to 3 edges — dangerous!
        dangerous = False
        for i in range(n):
            for j in range(n):
                # Skip already captured boxes
                if capture[i, j] != 0:
                    continue
                # Count filled edges for box (i,j)
                edges = [
                    h_temp[i, j],     # top
                    h_temp[i+1, j],   # bottom
                    v_temp[i, j],     # left
                    v_temp[i, j+1]    # right
                ]
                filled = sum(1 for e in edges if e != 0)
                if filled == 3:
                    dangerous = True
                    break
            if dangerous:
                break
        if not dangerous:
            safe_moves.append((r, c, d))

    if safe_moves:
        # Among safe moves, prefer outer edges or corners (less central)
        # Rank by "centrality": prefer low row/col or high indices (edges)
        def risk_score(r, c, d):
            # Higher score = more central = riskier
            return abs(r - 1.5) + abs(c - 1.5)  # 1.5 is center of 0..3
        safe_moves.sort(key=lambda x: risk_score(x[0], x[1], x[2]))  # prefer lower score (edges)
        r, c, d = safe_moves[0]
        return f"{r},{c},{d}"

    # Fallback: return first legal move (should not happen in practice)
    r, c, d = moves[0]
    return f"{r},{c},{d}"
