
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes (4x4 boxes => edges are 5x5 arrays).
    Returns a legal move string 'row,col,dir' where dir in {'H','V'}.
    """
    H = horizontal
    V = vertical
    C = capture  # not heavily used, but available

    def box_edges_status(r, c):
        # Box at (r,c), with r,c in 0..3
        # It uses:
        # - top horizontal:    H[r, c]
        # - bottom horizontal: H[r+1, c]
        # - left vertical:     V[r, c]
        # - right vertical:    V[r, c+1]
        top = H[r, c]
        bot = H[r+1, c]
        left = V[r, c]
        right = V[r, c+1]
        filled = (top != 0) + (bot != 0) + (left != 0) + (right != 0)
        return filled, (top != 0, bot != 0, left != 0, right != 0)

    # Generate all legal moves
    moves = []
    for r in range(5):
        for c in range(5):
            if H[r, c] == 0:
                moves.append((r, c, 'H'))
            if V[r, c] == 0:
                moves.append((r, c, 'V'))

    if not moves:
        # Should not happen in a legal game, but return some format-safe move
        return "0,0,H"

    def completes_box(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            # Horizontal edge at H[r,c] sits between boxes (r-1,c) and (r,c) if those exist.
            if r > 0 and 0 <= c < 4:
                boxes.append((r-1, c))
            if r < 4 and 0 <= c < 4:
                boxes.append((r, c))
        else:  # 'V'
            # Vertical edge at V[r,c] sits between boxes (r,c-1) and (r,c) if those exist.
            if c > 0 and 0 <= r < 4:
                boxes.append((r, c-1))
            if c < 4 and 0 <= r < 4:
                boxes.append((r, c))

        completed = 0
        would_make_threes = 0

        for br, bc in boxes:
            # Count edges already present for this box
            filled, _ = box_edges_status(br, bc)
            # If we add this edge, filled increases by 1 for exactly this box.
            # Since move is legal, this edge is currently absent.
            new_filled = filled + 1
            if filled == 3 and new_filled == 4:
                completed += 1
            # For "danger": if it doesn't complete, but makes it 3
            if new_filled == 3 and filled == 2:
                would_make_threes += 1
        return completed, would_make_threes

    # Prefer moves that capture (complete at least one box)
    capture_moves = []
    for mv in moves:
        comp, _ = completes_box(mv)
        if comp > 0:
            capture_moves.append((mv, comp))

    if capture_moves:
        # Choose capture move that captures the most boxes (usually 1, sometimes 2 or more)
        capture_moves.sort(key=lambda x: (-x[1], x[0][0], x[0][1], 0 if x[0][2]=='H' else 1))
        return f"{capture_moves[0][0][0]},{capture_moves[0][0][1]},{capture_moves[0][0][2]}"

    # No immediate capture: avoid moves that create any 3-sided box (danger moves)
    safe_moves = []
    danger_moves = []
    for mv in moves:
        _, make_threes = completes_box(mv)
        if make_threes == 0:
            safe_moves.append(mv)
        else:
            danger_moves.append((mv, make_threes))

    # Centrality heuristic to break ties among equally safe moves.
    # Prefer edges closer to the center of the 5x5 edge grid.
    center = np.array([2, 2], dtype=float)
    def centrality_score(mv):
        r, c, d = mv
        # distance from center in edge-grid coordinates
        dist = (r - center[0])**2 + (c - center[1])**2
        return dist

    if safe_moves:
        safe_moves.sort(key=lambda mv: (centrality_score(mv), 0 if mv[2]=='H' else 1, mv[0], mv[1]))
        mv = safe_moves[0]
        return f"{mv[0]},{mv[1]},{mv[2]}"

    # If no safe moves exist, pick the move that creates the fewest 3-sided boxes.
    # (This is a standard greedy defense.)
    danger_moves.sort(key=lambda x: (x[1], centrality_score(x[0]), 0 if x[0][2]=='H' else 1, x[0][0], x[0][1]))
    mv = danger_moves[0][0]
    return f"{mv[0]},{mv[1]},{mv[2]}"
