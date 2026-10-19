
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def get_legal_moves(h, v):
        moves = []
        for r in range(5):
            for c in range(4):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def count_sides(h, v, box_r, box_c):
        count = 0
        if h[box_r, box_c] != 0: count += 1
        if h[box_r + 1, box_c] != 0: count += 1
        if v[box_r, box_c] != 0: count += 1
        if v[box_r, box_c + 1] != 0: count += 1
        return count
    
    def get_affected_boxes(r, c, d):
        boxes = []
        if d == 'H':
            if r > 0: boxes.append((r - 1, c))
            if r < 4: boxes.append((r, c))
        else:  # V
            if c > 0: boxes.append((r, c - 1))
            if c < 4: boxes.append((r, c))
        return boxes
    
    def evaluate_move(h, v, r, c, d):
        captures = 0
        gives_away = 0
        affected = get_affected_boxes(r, c, d)
        for br, bc in affected:
            sides = count_sides(h, v, br, bc)
            if sides == 3:
                captures += 1
            elif sides == 2:
                gives_away += 1
        return captures, gives_away
    
    legal_moves = get_legal_moves(horizontal, vertical)
    
    if not legal_moves:
        return "0,0,H"  # Should never happen
    
    # Categorize moves
    capturing_moves = []
    safe_moves = []
    risky_moves = []
    
    for move in legal_moves:
        r, c, d = move
        captures, gives_away = evaluate_move(horizontal, vertical, r, c, d)
        if captures > 0:
            capturing_moves.append((move, captures, gives_away))
        elif gives_away == 0:
            safe_moves.append(move)
        else:
            risky_moves.append((move, gives_away))
    
    # Priority 1: Take captures (prefer moves that capture more and don't give away)
    if capturing_moves:
        # Sort by captures descending, then by gives_away ascending
        capturing_moves.sort(key=lambda x: (-x[1], x[2]))
        best = capturing_moves[0][0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Priority 2: Safe moves
    if safe_moves:
        # Prefer center moves slightly
        def center_score(m):
            r, c, d = m
            return -((r - 2) ** 2 + (c - 2) ** 2)
        safe_moves.sort(key=center_score, reverse=True)
        best = safe_moves[0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Priority 3: Must give away - minimize damage
    if risky_moves:
        # Give away the least number of boxes
        risky_moves.sort(key=lambda x: x[1])
        best = risky_moves[0][0]
        return f"{best[0]},{best[1]},{best[2]}"
    
    # Fallback
    best = legal_moves[0]
    return f"{best[0]},{best[1]},{best[2]}"
