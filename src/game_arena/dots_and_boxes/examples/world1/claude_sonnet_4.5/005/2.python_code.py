
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy using strategic heuristics.
    """
    
    def count_box_edges(r, c):
        """Count how many edges of box (r,c) are already drawn."""
        if r >= 4 or c >= 4:
            return -1
        count = 0
        if horizontal[r, c] != 0: count += 1      # top
        if horizontal[r+1, c] != 0: count += 1    # bottom
        if vertical[r, c] != 0: count += 1        # left
        if vertical[r, c+1] != 0: count += 1      # right
        return count
    
    def completes_box(r, c, is_horizontal):
        """Check if a move completes any box and return count."""
        completed = 0
        if is_horizontal:
            # Check box above
            if r > 0 and capture[r-1, c] == 0:
                if count_box_edges(r-1, c) == 3:
                    completed += 1
            # Check box below
            if r < 4 and capture[r, c] == 0:
                if count_box_edges(r, c) == 3:
                    completed += 1
        else:  # vertical
            # Check box to the left
            if c > 0 and capture[r, c-1] == 0:
                if count_box_edges(r, c-1) == 3:
                    completed += 1
            # Check box to the right
            if c < 4 and capture[r, c] == 0:
                if count_box_edges(r, c) == 3:
                    completed += 1
        return completed
    
    def creates_three_sided_box(r, c, is_horizontal):
        """Check if a move creates a 3-sided box (dangerous)."""
        if is_horizontal:
            # Check box above
            if r > 0 and capture[r-1, c] == 0:
                if count_box_edges(r-1, c) == 2:
                    return True
            # Check box below
            if r < 4 and capture[r, c] == 0:
                if count_box_edges(r, c) == 2:
                    return True
        else:  # vertical
            # Check box to the left
            if c > 0 and capture[r, c-1] == 0:
                if count_box_edges(r, c-1) == 2:
                    return True
            # Check box to the right
            if c < 4 and capture[r, c] == 0:
                if count_box_edges(r, c) == 2:
                    return True
        return False
    
    # Collect all legal moves
    capturing_moves = []
    safe_moves = []
    dangerous_moves = []
    
    for r in range(5):
        for c in range(5):
            # Check horizontal edge
            if horizontal[r, c] == 0:
                boxes_completed = completes_box(r, c, True)
                if boxes_completed > 0:
                    capturing_moves.append((r, c, 'H', boxes_completed))
                elif creates_three_sided_box(r, c, True):
                    dangerous_moves.append((r, c, 'H'))
                else:
                    safe_moves.append((r, c, 'H'))
            
            # Check vertical edge
            if vertical[r, c] == 0:
                boxes_completed = completes_box(r, c, False)
                if boxes_completed > 0:
                    capturing_moves.append((r, c, 'V', boxes_completed))
                elif creates_three_sided_box(r, c, False):
                    dangerous_moves.append((r, c, 'V'))
                else:
                    safe_moves.append((r, c, 'V'))
    
    # Decision logic
    # 1. Always capture if possible
    if capturing_moves:
        # Prefer moves that capture more boxes
        capturing_moves.sort(key=lambda x: x[3], reverse=True)
        r, c, d, _ = capturing_moves[0]
        return f"{r},{c},{d}"
    
    # 2. Play safe moves if available
    if safe_moves:
        # Prefer moves on boxes with fewer edges (safer for future)
        def safety_score(move):
            r, c, d = move
            adjacent_boxes = []
            if d == 'H':
                if r > 0: adjacent_boxes.append(count_box_edges(r-1, c))
                if r < 4: adjacent_boxes.append(count_box_edges(r, c))
            else:
                if c > 0: adjacent_boxes.append(count_box_edges(r, c-1))
                if c < 4: adjacent_boxes.append(count_box_edges(r, c))
            return min(adjacent_boxes) if adjacent_boxes else 0
        
        safe_moves.sort(key=safety_score)
        r, c, d = safe_moves[0]
        return f"{r},{c},{d}"
    
    # 3. No safe moves - must play dangerous move
    if dangerous_moves:
        # Try to minimize damage - prefer giving away smaller chains
        r, c, d = dangerous_moves[0]
        return f"{r},{c},{d}"
    
    # 4. Fallback - should never reach here if game is still valid
    # Return any legal move
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
            if vertical[r, c] == 0:
                return f"{r},{c},V"
    
    # Ultimate fallback
    return "0,0,H"
