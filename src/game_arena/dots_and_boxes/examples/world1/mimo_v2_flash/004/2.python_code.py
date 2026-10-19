
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy for a 4x4 grid.
    Prioritizes capturing boxes, then safe moves (avoiding 3-side boxes), 
    then minimizes risk.
    """
    rows, cols = horizontal.shape
    h_rows, h_cols = rows, cols - 1
    v_rows, v_cols = rows - 1, cols
    
    # Identify all legal moves (empty edges)
    legal_moves = []
    
    # Helper to check if a move completes a box
    def get_completed_boxes(r, c, direction):
        completed = []
        # Coordinates are grid coordinates (0-4 for 4x4 boxes)
        if direction == 'H':
            # Horizontal edge at (r, c) connects dots (r,c) and (r,c+1)
            # It borders box (r-1, c) above and (r, c) below
            # Check above
            if r > 0:
                # Box (r-1, c) has top edge (r,c), bottom (r-1,c), left (r-1,c), right (r-1,c+1)
                # Edges in arrays: H[r,c] (top), H[r-1,c] (bot), V[r-1,c] (left), V[r-1,c+1] (right)
                if H[r, c] != 0 and H[r-1, c] != 0 and V[r-1, c] != 0 and V[r-1, c+1] != 0:
                    completed.append((r-1, c))
            # Check below
            if r < h_rows - 1:
                # Box (r, c) has top edge (r,c), bottom (r+1,c), left (r,c), right (r,c+1)
                if H[r, c] != 0 and H[r+1, c] != 0 and V[r, c] != 0 and V[r, c+1] != 0:
                    completed.append((r, c))
                    
        elif direction == 'V':
            # Vertical edge at (r, c) connects dots (r,c) and (r+1,c)
            # It borders box (r, c-1) left and (r, c) right
            # Check left
            if c > 0:
                # Box (r, c-1) has right edge (r,c), left (r,c-1), top (r,c-1), bottom (r+1,c-1)
                if V[r, c] != 0 and V[r, c-1] != 0 and H[r, c-1] != 0 and H[r+1, c-1] != 0:
                    completed.append((r, c-1))
            # Check right
            if c < v_cols - 1:
                # Box (r, c) has left edge (r,c), right (r,c+1), top (r,c), bottom (r+1,c)
                if V[r, c] != 0 and V[r, c+1] != 0 and H[r, c] != 0 and H[r+1, c] != 0:
                    completed.append((r, c))
        return completed

    # Helper to count potential created 3-edge boxes
    def count_3_edge_boxes(r, c, direction):
        count = 0
        if direction == 'H':
            # Above
            if r > 0:
                edges = [H[r,c], H[r-1,c], V[r-1,c], V[r-1,c+1]]
                # If exactly 3 are non-zero (excluding the one we are about to draw)
                if sum(1 for x in edges if x != 0) == 3:
                    count += 1
            # Below
            if r < h_rows - 1:
                edges = [H[r,c], H[r+1,c], V[r,c], V[r,c+1]]
                if sum(1 for x in edges if x != 0) == 3:
                    count += 1
        elif direction == 'V':
            # Left
            if c > 0:
                edges = [V[r,c], V[r,c-1], H[r,c-1], H[r+1,c-1]]
                if sum(1 for x in edges if x != 0) == 3:
                    count += 1
            # Right
            if c < v_cols - 1:
                edges = [V[r,c], V[r,c+1], H[r,c], H[r+1,c]]
                if sum(1 for x in edges if x != 0) == 3:
                    count += 1
        return count

    # Local references to arrays for cleaner access
    H = horizontal
    V = vertical

    # 1. Find all legal moves and score them
    candidates = []

    # Check Horizontal Edges
    for r in range(h_rows):
        for c in range(h_cols):
            if H[r, c] == 0:
                # Check if it completes boxes
                boxes = get_completed_boxes(r, c, 'H')
                boxes_count = len(boxes)
                
                # Calculate risk (created 3-edge boxes)
                risk = count_3_edge_boxes(r, c, 'H')
                
                candidates.append({
                    'move': f"{r},{c},H",
                    'score': boxes_count * 100 - risk,  # Prioritize capture massively
                    'captures': boxes_count,
                    'risk': risk
                })

    # Check Vertical Edges
    for r in range(v_rows):
        for c in range(v_cols):
            if V[r, c] == 0:
                boxes = get_completed_boxes(r, c, 'V')
                boxes_count = len(boxes)
                risk = count_3_edge_boxes(r, c, 'V')
                
                candidates.append({
                    'move': f"{r},{c},V",
                    'score': boxes_count * 100 - risk,
                    'captures': boxes_count,
                    'risk': risk
                })

    if not candidates:
        # Should not happen if called correctly, but safety net
        return "0,0,H" 

    # 2. Select the best move
    # Sort by score (descending), then risk (ascending)
    candidates.sort(key=lambda x: (x['score'], -x['risk']), reverse=True)
    
    best_move = candidates[0]['move']
    return best_move
