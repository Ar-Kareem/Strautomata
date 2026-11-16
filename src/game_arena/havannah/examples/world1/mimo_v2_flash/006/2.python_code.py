
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah Policy: Aggressive Heuristic Strategy
    Focuses on connectivity, blocking, and center/corner control.
    """
    
    # --- 1. Configuration ---
    BOARD_SIZE = 15
    
    # Corner coordinates (Row, Col) in the 2D grid representation
    # In Odd-R offset, corners are at these indices.
    CORNERS = [
        (0, 0), (0, 14), (14, 0), (14, 14), 
        (7, 0), (7, 14)
    ]
    
    # Center of the board
    CENTER = (7, 7)
    
    # Heuristic weights
    WEIGHT_CONNECT = 1.5   # Encourages forming clusters
    WEIGHT_BLOCK   = 1.2   # Discourages opponent expansion
    WEIGHT_CENTER  = 0.05  # Encourages central control
    WEIGHT_CORNER  = 0.1   # Encourages reaching corners for Bridges/Forks
    
    # --- 2. Helper: Hex Neighbors in Odd-R Offset ---
    def get_hex_neighbors(r, c):
        """Returns valid neighbors for a hex grid in Odd-R offset layout."""
        # Even rows shift left, Odd rows shift right is standard, 
        # but here we define offsets based on standard hex neighbor logic
        # converted to 2D grid offsets.
        is_even = (r % 2 == 0)
        offsets = []
        
        if is_even:
            # Even row: Neighbors are (r, c-1), (r, c+1), (r-1, c-1), (r-1, c), (r+1, c-1), (r+1, c)
            offsets = [
                (0, -1), (0, 1), (-1, -1), (-1, 0), (1, -1), (1, 0)
            ]
        else:
            # Odd row: Neighbors are (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c+1)
            offsets = [
                (0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, 1)
            ]
            
        neighbors = []
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors

    # --- 3. Setup Sets for Fast Lookup ---
    me_set = set(me)
    opp_set = set(opp)
    
    # --- 4. Evaluation Loop ---
    best_score = -float('inf')
    best_move = None
    
    # Iterate over all valid moves
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if not valid_mask[r][c]:
                continue
            
            # Skip occupied cells
            if (r, c) in me_set or (r, c) in opp_set:
                continue
            
            score = 0.0
            
            # A. Connectivity & Blocking
            neighbors = get_hex_neighbors(r, c)
            for nr, nc in neighbors:
                if (nr, nc) in me_set:
                    score += WEIGHT_CONNECT
                elif (nr, nc) in opp_set:
                    score += WEIGHT_BLOCK
            
            # B. Center Control (Euclidean distance)
            dist_center = abs(r - CENTER[0]) + abs(c - CENTER[1])
            score += WEIGHT_CENTER * (10 - dist_center) # Higher score for closer
            
            # C. Corner Control (Sum of distances to 6 corners)
            # Being near corners facilitates Bridges and Forks
            corner_score = 0
            for corner in CORNERS:
                # Hex distance approximation or Manhattan
                dist_corner = max(abs(r - corner[0]), abs(c - corner[1]))
                corner_score += (14 - dist_corner) 
            score += WEIGHT_CORNER * (corner_score / 6.0)
            
            # D. Random Tie-breaker to ensure deterministic behavior
            score += (r * 0.0001) + (c * 0.00001)
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
                
    # Fallback (should not happen if valid_mask is valid)
    if best_move is None:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if valid_mask[r][c]:
                    return (r, c)
                    
    return best_move
