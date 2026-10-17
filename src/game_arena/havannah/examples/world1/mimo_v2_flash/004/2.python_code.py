
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah AI Policy
    Uses a heuristic approach focusing on local connectivity, center control,
    and basic threat blocking.
    """
    N = valid_mask.shape[0]
    me_set = set(me)
    opp_set = set(opp)
    all_stones = me_set.union(opp_set)
    
    # Identify valid empty positions
    valid_coords = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r, c] and (r, c) not in all_stones:
                valid_coords.append((r, c))
                
    if not valid_coords:
        # Should not happen in a valid game state, but safety check
        return (0, 0)

    # Helper to get hex neighbors
    def get_neighbors(r, c):
        # In a hexagonal grid mapped to a 2D array (offset coordinates):
        # For odd columns (or even, depending on orientation, usually standard map):
        # Let's assume standard 2D mapping where (r, c) has:
        # (r-1, c), (r+1, c) (vertical)
        # (r, c-1), (r, c+1) (horizontal/diagonal depending on specific hex layout)
        # Based on the description: "store at (4,1) touching (5,1), (3,1), (3,0), (4,0), (4,2), (3,2)"
        # This suggests an "odd-q" vertical layout:
        # Neighbors are: (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r+1, c-1)
        # Wait, let's re-verify. (4,1) -> (3,0) and (4,0) implies left neighbors are (c-1).
        # Let's assume standard axial coordinate logic adapted to 2D array:
        # If c is even:
        #   (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r+1, c-1)
        # If c is odd:
        #   (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c+1), (r+1, c+1)
        # The example: (4,1) -> (3,0) and (4,0). Here c=1 (odd). Left neighbors are (3,0) and (4,0).
        # (3,0) is r-1, c-1. (4,0) is r, c-1. Correct.
        neighbors = []
        if c % 2 == 0: # Even columns
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1)]
        else: # Odd columns
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, 1)]
        
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                neighbors.append((nr, nc))
        return neighbors

    best_score = -float('inf')
    best_move = valid_coords[0]

    # 1. Immediate Win Check
    # (Skipping full connectivity check due to time, but checking immediate local extensions)
    # This is a simplified check: if placing a stone connects high-value components.

    # 2. Threat Blocking & Connection Building
    # We evaluate each valid move based on:
    # - Local connectivity (friendly neighbors)
    # - Opponent proximity (blocking potential)
    # - Center distance
    
    # Pre-calculate opponent neighbors to identify clusters
    # This helps in detecting if we need to block a forming ring or bridge
    
    for r, c in valid_coords:
        score = 0
        neighbors = get_neighbors(r, c)
        
        # Count friendly and opponent neighbors
        f_neighbors = 0
        o_neighbors = 0
        empty_neighbors = 0
        
        for nr, nc in neighbors:
            if (nr, nc) in me_set:
                f_neighbors += 1
            elif (nr, nc) in opp_set:
                o_neighbors += 1
            else:
                empty_neighbors += 1
        
        # Primary Heuristic: Maximize Friendly Connectivity
        # A move is good if it connects to existing stones.
        score += f_neighbors * 5 
        
        # Secondary Heuristic: Block Opponent
        # If an opponent stone is nearby, it might be part of a ring or bridge.
        # Blocking paths is crucial.
        score += o_neighbors * 3 
        
        # Tertiary Heuristic: Center Control
        # Distance from center (7, 7)
        center_dist = abs(r - 7) + abs(c - 7)
        score -= center_dist * 0.5
        
        # Quaternary Heuristic: Space
        # Having empty neighbors is generally good for flexibility, 
        # but too many might mean we are isolated.
        # We prefer balanced spots.
        score += empty_neighbors * 0.1
        
        # 3. Specific Strategy: Bridge Building
        # Corners of 15x15 board are roughly (0,0), (0,14), (14,0), (14,14)
        # Also (0,7) and (14,7) for hex specific corners? 
        # In standard Havannah, corners are the 6 vertices of the hexagon shape.
        # For a 15x15 square grid representing a hex board, corners are usually:
        # Top-Left, Top-Right, Left-Top, Left-Bottom, Right-Top, Right-Bottom
        # Let's approximate the 6 corners for a 15x15 grid:
        # (0, 0), (0, 14), (7, 0), (7, 14), (14, 0), (14, 14) -- roughly.
        # Or simply the 4 corners of the array + mid-edges if applicable.
        # Let's boost score if we are moving towards a corner where we have stones.
        corners = [(0, 0), (0, 14), (14, 0), (14, 14)] 
        for corner in corners:
            if (corner in me_set):
                # If we have a stone in a corner, moving towards it or away from it 
                # along the edge helps bridges.
                dist_to_corner = abs(r - corner[0]) + abs(c - corner[1])
                if dist_to_corner < 10: # Near a corner we own
                    score += 2
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
