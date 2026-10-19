
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy that prioritizes capturing boxes,
    avoiding giving away boxes, and making safe moves.
    """
    
    def count_box_sides(r, c):
        """Count how many sides of box (r,c) are already drawn."""
        if r < 0 or r > 3 or c < 0 or c > 3:
            return -1
        count = 0
        if horizontal[r, c] != 0: count += 1      # top
        if horizontal[r+1, c] != 0: count += 1    # bottom
        if vertical[r, c] != 0: count += 1        # left
        if vertical[r, c+1] != 0: count += 1      # right
        return count
    
    def completes_box(r, c, direction):
        """Check if playing this edge completes any boxes."""
        completed = []
        if direction == 'H':
            # Check box above (r-1, c)
            if r > 0 and capture[r-1, c] == 0 and count_box_sides(r-1, c) == 3:
                completed.append((r-1, c))
            # Check box below (r, c)
            if r < 4 and capture[r, c] == 0 and count_box_sides(r, c) == 3:
                completed.append((r, c))
        else:  # 'V'
            # Check box left (r, c-1)
            if c > 0 and capture[r, c-1] == 0 and count_box_sides(r, c-1) == 3:
                completed.append((r, c-1))
            # Check box right (r, c)
            if c < 4 and capture[r, c] == 0 and count_box_sides(r, c) == 3:
                completed.append((r, c))
        return completed
    
    def creates_three_sided_box(r, c, direction):
        """Check if playing this edge creates a 3-sided box (gift to opponent)."""
        if direction == 'H':
            # Check box above (r-1, c)
            if r > 0 and capture[r-1, c] == 0 and count_box_sides(r-1, c) == 2:
                return True
            # Check box below (r, c)
            if r < 4 and capture[r, c] == 0 and count_box_sides(r, c) == 2:
                return True
        else:  # 'V'
            # Check box left (r, c-1)
            if c > 0 and capture[r, c-1] == 0 and count_box_sides(r, c-1) == 2:
                return True
            # Check box right (r, c)
            if c < 4 and capture[r, c] == 0 and count_box_sides(r, c) == 2:
                return True
        return False
    
    def get_legal_moves():
        """Get all legal moves."""
        moves = []
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    legal_moves = get_legal_moves()
    
    if not legal_moves:
        return "0,0,H"  # Should never happen
    
    # Phase 1: Complete boxes if possible (always good to score)
    completing_moves = []
    for r, c, d in legal_moves:
        completed = completes_box(r, c, d)
        if completed:
            completing_moves.append((r, c, d, len(completed)))
    
    if completing_moves:
        # Choose move that completes the most boxes
        completing_moves.sort(key=lambda x: x[3], reverse=True)
        r, c, d, _ = completing_moves[0]
        return f"{r},{c},{d}"
    
    # Phase 2: Avoid creating 3-sided boxes (safe moves)
    safe_moves = []
    risky_moves = []
    
    for r, c, d in legal_moves:
        if creates_three_sided_box(r, c, d):
            risky_moves.append((r, c, d))
        else:
            safe_moves.append((r, c, d))
    
    # Prefer safe moves
    if safe_moves:
        # Among safe moves, prefer those adjacent to boxes with fewer sides
        def safe_move_score(move):
            r, c, d = move
            min_sides = 4
            if d == 'H':
                if r > 0: min_sides = min(min_sides, count_box_sides(r-1, c))
                if r < 4: min_sides = min(min_sides, count_box_sides(r, c))
            else:
                if c > 0: min_sides = min(min_sides, count_box_sides(r, c-1))
                if c < 4: min_sides = min(min_sides, count_box_sides(r, c))
            return min_sides
        
        safe_moves.sort(key=safe_move_score)
        r, c, d = safe_moves[0]
        return f"{r},{c},{d}"
    
    # Phase 3: All moves create 3-sided boxes (forced to give away)
    # Choose the move that minimizes damage
    if risky_moves:
        r, c, d = risky_moves[0]
        return f"{r},{c},{d}"
    
    # Fallback: just return first legal move
    r, c, d = legal_moves[0]
    return f"{r},{c},{d}"
