
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next target (row, col) for a Battleship game on a 10x10 grid.
    
    Board State:
     0: Unknown
     1: Hit
    -1: Miss
    
    Strategy:
    Uses a Probability Density Function (Heatmap).
    It iterates through all possible valid placements of the standard ships (5, 4, 3, 3, 2).
    - Placements overlapping existing 'Hits' contribute to a 'Target Density', weighted by number of hits covered.
    - Placements in open water contribute to a 'Hunt Density'.
    
    The policy prioritizes:
    1. High-confidence targets (extensions of existing hit chains).
    2. Parity-based hunting (checkerboard pattern) on high-probability areas.
    """
    rows = 10
    cols = 10
    ships = [5, 4, 3, 3, 2]
    
    # Parse board
    grid = np.array(board)
    
    # Initialize separate probability maps
    # target_prob: Score for cells that are part of a potential ship passing through known hits.
    # hunt_prob: Score for cells that are part of a potential ship in open water.
    target_prob = np.zeros((rows, cols), dtype=float)
    hunt_prob = np.zeros((rows, cols), dtype=float)
    
    # Iterate through all ship lengths and all positions
    for length in ships:
        # Check Horizontal Placements
        for r in range(rows):
            for c in range(cols - length + 1):
                # Extract the segment of the board
                segment = grid[r, c : c + length]
                
                # Validity check: A ship cannot sit on a Miss (-1)
                if np.any(segment == -1):
                    continue
                
                # Count overlaps with existing hits
                hit_count = np.sum(segment == 1)
                
                if hit_count > 0:
                    # This placement explains 'hit_count' existing hits.
                    # We heavily weight placements that explain more hits.
                    # e.g., A placement fitting 3 hits is far more likely than one fitting 1.
                    weight = 1000 * (hit_count ** 3)
                    
                    # Add weight to the unknown cells in this segment
                    # (We don't need to target cells that are already 1 or -1)
                    for i in range(length):
                        if segment[i] == 0:
                            target_prob[r, c + i] += weight
                else:
                    # This placement is in open water (Hunt mode)
                    weight = 1
                    for i in range(length):
                        if segment[i] == 0:
                            hunt_prob[r, c + i] += weight

        # Check Vertical Placements
        for r in range(rows - length + 1):
            for c in range(cols):
                segment = grid[r : r + length, c]
                
                if np.any(segment == -1):
                    continue
                
                hit_count = np.sum(segment == 1)
                
                if hit_count > 0:
                    weight = 1000 * (hit_count ** 3)
                    for i in range(length):
                        if segment[i] == 0:
                            target_prob[r + i, c] += weight
                else:
                    weight = 1
                    for i in range(length):
                        if segment[i] == 0:
                            hunt_prob[r + i, c] += weight

    # Add small random noise to break ties deterministically but unpredictably
    jitter = np.random.rand(rows, cols) * 0.1
    target_prob += jitter
    hunt_prob += jitter

    # Decision Phase
    
    # 1. Target Mode: If we have high probability targets attached to existing hits, fire there.
    # We use a threshold to ensure we aren't just looking at jitter.
    max_target = np.max(target_prob)
    if max_target > 1.0:
        best_idx = np.unravel_index(np.argmax(target_prob), (rows, cols))
        return int(best_idx[0]), int(best_idx[1])
    
    # 2. Hunt Mode: No active targets. Search for ships.
    # Optimization: Use Checkerboard Parity. 
    # Since smallest ship is 2, we only need to fire at (r+c)%2 == 0 to find all ships.
    indices = np.indices((rows, cols))
    checkerboard_mask = (indices[0] + indices[1]) % 2 == 0
    
    masked_hunt = hunt_prob * checkerboard_mask
    max_hunt = np.max(masked_hunt)
    
    if max_hunt > 1.0:
        best_idx = np.unravel_index(np.argmax(masked_hunt), (rows, cols))
        return int(best_idx[0]), int(best_idx[1])
        
    # 3. Fallback: If checkerboard masked everything (unlikely, e.g. only odd cells left), use raw hunt prob.
    best_idx = np.unravel_index(np.argmax(hunt_prob), (rows, cols))
    
    # 4. Ultimate Fallback: Just pick the first available unknown cell
    if hunt_prob[best_idx] < 0.5:
        unknowns = np.argwhere(grid == 0)
        if len(unknowns) > 0:
            # Pick a random unknown to avoid stuck states
            choice = unknowns[np.random.randint(len(unknowns))]
            return int(choice[0]), int(choice[1])
            
    return int(best_idx[0]), int(best_idx[1])
