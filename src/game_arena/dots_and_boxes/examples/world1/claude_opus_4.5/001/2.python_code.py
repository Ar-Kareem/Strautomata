
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def get_legal_moves():
        moves = []
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def count_box_edges(r, c, h, v):
        count = 0
        if h[r, c] != 0: count += 1
        if h[r+1, c] != 0: count += 1
        if v[r, c] != 0: count += 1
        if v[r, c+1] != 0: count += 1
        return count
    
    def boxes_completed_by_move(r, c, d, h, v):
        completed = []
        if d == 'H':
            if r > 0 and count_box_edges(r-1, c, h, v) == 3:
                completed.append((r-1, c))
            if r < 4 and count_box_edges(r, c, h, v) == 3:
                completed.append((r, c))
        else:
            if c > 0 and count_box_edges(r, c-1, h, v) == 3:
                completed.append((r, c-1))
            if c < 4 and count_box_edges(r, c, h, v) == 3:
                completed.append((r, c))
        return completed
    
    def boxes_with_3_edges_after_move(r, c, d, h, v):
        count = 0
        if d == 'H':
            if r > 0 and count_box_edges(r-1, c, h, v) == 2:
                count += 1
            if r < 4 and count_box_edges(r, c, h, v) == 2:
                count += 1
        else:
            if c > 0 and count_box_edges(r, c-1, h, v) == 2:
                count += 1
            if c < 4 and count_box_edges(r, c, h, v) == 2:
                count += 1
        return count
    
    legal_moves = get_legal_moves()
    
    if not legal_moves:
        return "0,0,H"
    
    # Priority 1: Moves that complete boxes
    capturing_moves = []
    for move in legal_moves:
        r, c, d = move
        completed = boxes_completed_by_move(r, c, d, horizontal, vertical)
        if completed:
            capturing_moves.append((move, len(completed)))
    
    if capturing_moves:
        capturing_moves.sort(key=lambda x: -x[1])
        best = capturing_moves[0][0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Priority 2: Safe moves that don't create 3-sided boxes
    safe_moves = []
    risky_moves = []
    
    for move in legal_moves:
        r, c, d = move
        danger = boxes_with_3_edges_after_move(r, c, d, horizontal, vertical)
        if danger == 0:
            safe_moves.append(move)
        else:
            risky_moves.append((move, danger))
    
    if safe_moves:
        # Prefer moves in center area
        def score_safe(m):
            r, c, d = m
            center_dist = abs(r - 2) + abs(c - 2)
            return center_dist
        safe_moves.sort(key=score_safe)
        best = safe_moves[0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Priority 3: Must give away boxes - minimize damage
    risky_moves.sort(key=lambda x: x[1])
    best = risky_moves[0][0]
    return f"{best[0]},{best[1]},{best[2]}"
