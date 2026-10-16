
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a Battleship game.
    
    Args:
        board: A 10x10 grid where:
             0 -> Unknown
            -1 -> Miss
             1 -> Hit
             
    Returns:
        (row, col) coordinates to fire at.
    """
    rows = 10
    cols = 10
    # Standard fleet sizes. Even if ships are sunk, simulating them 
    # reinforces the 'completed' structure logic without breaking targeting.
    ships = [5, 4, 3, 3, 2]
    
    # Initialize probability map with tiny random noise for tie-breaking
    prob_map = [[random.uniform(0, 1e-6) for _ in range(cols)] for _ in range(rows)]
    max_prob = 0.0
    
    # Helper to calculate the 'weight' of a specific ship placement
    def get_placement_weight(r, c, dr, dc, length):
        hits = 0
        for k in range(length):
            # Coordinates of the k-th segment of the ship
            cr, cc = r + k * dr, c + k * dc
            cell = board[cr][cc]
            
            if cell == -1: 
                # Placement overlaps a Miss -> Invalid
                return 0
            if cell == 1:
                # Placement overlaps a Hit -> Valid and evidence supporting this placement
                hits += 1
        
        # Scoring logic:
        # If hits > 0, we are in "Target/Kill" mode. Boost weight significantly 
        # so these cells dominate the probability map.
        # Prefer placements that explain MORE hits (10^hits).
        if hits > 0:
            return 10_000 * (100 ** hits)
        else:
            # "Hunt" mode: standard probability
            return 1

    # Simulate all possible ship placements
    for length in ships:
        # Horizontal placements
        for r in range(rows):
            for c in range(cols - length + 1):
                weight = get_placement_weight(r, c, 0, 1, length)
                if weight > 0:
                    # Distribute weight to all UNKNOWN cells in this footprint
                    for k in range(length):
                        cc = c + k
                        if board[r][cc] == 0:
                            prob_map[r][cc] += weight
                            if prob_map[r][cc] > max_prob:
                                max_prob = prob_map[r][cc]

        # Vertical placements
        for c in range(cols):
            for r in range(rows - length + 1):
                weight = get_placement_weight(r, c, 1, 0, length)
                if weight > 0:
                    for k in range(length):
                        rr = r + k
                        if board[rr][c] == 0:
                            prob_map[rr][c] += weight
                            if prob_map[rr][c] > max_prob:
                                max_prob = prob_map[rr][c]

    # Determine mode based on max probability found
    # If max_prob < 5000, no placement covered a Hit. We are hunting.
    hunting = max_prob < 5000
    
    best_cell = None
    best_val = -1.0
    
    # Selection:
    # If Hunting, apply Checkerboard Parity to reduce search space.
    if hunting:
        for r in range(rows):
            for c in range(cols):
                if board[r][c] != 0: continue
                
                # Check parity (only fire on even sums)
                if (r + c) % 2 != 0: continue
                
                if prob_map[r][c] > best_val:
                    best_val = prob_map[r][c]
                    best_cell = (r, c)
                    
    # Fallback / Target Mode:
    # If we are targeting (not hunting), or if hunting found no valid parity moves
    # (e.g., all even squares are shot), select the absolute max probability.
    if best_cell is None:
        best_val = -1.0
        for r in range(rows):
            for c in range(cols):
                if board[r][c] != 0: continue
                
                if prob_map[r][c] > best_val:
                    best_val = prob_map[r][c]
                    best_cell = (r, c)
    
    # Final safety fallback (random valid zero)
    if best_cell is None:
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == 0:
                    return (r, c)

    return best_cell
