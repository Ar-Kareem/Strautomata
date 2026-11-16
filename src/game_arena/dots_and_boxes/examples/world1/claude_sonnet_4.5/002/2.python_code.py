
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy using strategic principles.
    """
    
    def count_box_edges(r, c):
        """Count how many edges a box has (0-4)."""
        if r < 0 or r > 3 or c < 0 or c > 3:
            return 0
        count = 0
        if horizontal[r, c] != 0: count += 1      # top
        if horizontal[r+1, c] != 0: count += 1    # bottom
        if vertical[r, c] != 0: count += 1        # left
        if vertical[r, c+1] != 0: count += 1      # right
        return count
    
    def move_completes_boxes(row, col, is_horizontal):
        """Check how many boxes this move would complete."""
        completed = 0
        if is_horizontal:
            # Check box above
            if row > 0 and capture[row-1, col] == 0:
                if count_box_edges(row-1, col) == 3:
                    completed += 1
            # Check box below
            if row < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 3:
                    completed += 1
        else:  # vertical
            # Check box to the left
            if col > 0 and capture[row, col-1] == 0:
                if count_box_edges(row, col-1) == 3:
                    completed += 1
            # Check box to the right
            if col < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 3:
                    completed += 1
        return completed
    
    def move_creates_three_sided(row, col, is_horizontal):
        """Check if this move creates any 3-sided boxes."""
        if is_horizontal:
            # Check box above
            if row > 0 and capture[row-1, col] == 0:
                if count_box_edges(row-1, col) == 2:
                    return True
            # Check box below
            if row < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 2:
                    return True
        else:  # vertical
            # Check box to the left
            if col > 0 and capture[row, col-1] == 0:
                if count_box_edges(row, col-1) == 2:
                    return True
            # Check box to the right
            if col < 4 and capture[row, col] == 0:
                if count_box_edges(row, col) == 2:
                    return True
        return False
    
    # Collect all legal moves
    capture_moves = []
    safe_moves = []
    unsafe_moves = []
    
    # Check horizontal edges
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                completes = move_completes_boxes(r, c, True)
                if completes > 0:
                    capture_moves.append((r, c, 'H', completes))
                elif not move_creates_three_sided(r, c, True):
                    safe_moves.append((r, c, 'H'))
                else:
                    unsafe_moves.append((r, c, 'H'))
    
    # Check vertical edges
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                completes = move_completes_boxes(r, c, False)
                if completes > 0:
                    capture_moves.append((r, c, 'V', completes))
                elif not move_creates_three_sided(r, c, False):
                    safe_moves.append((r, c, 'V'))
                else:
                    unsafe_moves.append((r, c, 'V'))
    
    # Priority 1: Take any boxes we can capture
    if capture_moves:
        # Sort by number of boxes completed (descending)
        capture_moves.sort(key=lambda x: x[3], reverse=True)
        move = capture_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    # Priority 2: Make safe moves (don't create 3-sided boxes)
    if safe_moves:
        # Prefer central moves early in the game
        def move_score(m):
            r, c, d = m
            # Prefer edges closer to center
            if d == 'H':
                center_dist = abs(r - 2) + abs(c - 2)
            else:
                center_dist = abs(r - 2) + abs(c - 2)
            return -center_dist  # Negative so closer to center is better
        
        safe_moves.sort(key=move_score, reverse=True)
        move = safe_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    # Priority 3: No safe moves left, choose the least bad unsafe move
    # Try to give away as few boxes as possible
    if unsafe_moves:
        # Choose move that creates fewest immediate capture opportunities
        move = unsafe_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    # Fallback: return any legal move (should never reach here)
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
            if vertical[r, c] == 0:
                return f"{r},{c},V"
    
    return "0,0,H"  # Ultimate fallback
