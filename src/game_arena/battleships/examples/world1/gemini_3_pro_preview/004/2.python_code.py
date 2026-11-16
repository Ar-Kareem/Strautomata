
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy using Probability Density Functions (PDF).
    
    The algorithm calculates the most likely location of a ship by summing the 
    probabilities of all valid ship placements consistent with the current board state.
    It transitions seamlessly between 'Targeting' (expanding on hits) and 'Hunting' 
    (searching open water).
    """
    
    # Board Constants: 0 -> Unknown, -1 -> Miss, 1 -> Hit
    ROWS, COLS = 10, 10
    grid = np.array(board)
    ships = [5, 4, 3, 3, 2] # Standard Battleship fleet
    
    # Initialize probability map
    # This grid accumulates the likelihood of each cell containing a ship
    prob_map = np.zeros((ROWS, COLS), dtype=float)
    
    # Weight Constants
    BASE_WEIGHT = 1.0           # Likelihood for a placement in open water
    HIT_BONUS = 1000.0          # Massive bonus for placements explaining existing hits
    HIT_MULTIPLIER = 100.0      # Additional bonus per hit to favor longer alignments
    
    # Iterate through every ship size and every possible orientation/position
    for ship_len in ships:
        
        # 1. Horizontal placements
        # Ship occupies [r, c] to [r, c + ship_len - 1]
        for r in range(ROWS):
            for c in range(COLS - ship_len + 1):
                segment = grid[r, c : c + ship_len]
                
                # Invalid placement if it overlaps a Miss (-1)
                if np.any(segment == -1):
                    continue
                
                # Check for Hits in this placement
                num_hits = np.sum(segment == 1)
                
                # Calculate Weight
                if num_hits > 0:
                    # High weight: This placement explains observed hits
                    weight = HIT_BONUS + (HIT_MULTIPLIER * num_hits)
                else:
                    # Base weight: Possible location in hunt mode
                    weight = BASE_WEIGHT
                
                # Add weight to probability map for all UNKNOWN cells in this segment
                for i in range(ship_len):
                    if segment[i] == 0:
                        prob_map[r, c + i] += weight

        # 2. Vertical placements
        # Ship occupies [r, c] to [r + ship_len - 1, c]
        for c in range(COLS):
            for r in range(ROWS - ship_len + 1):
                segment = grid[r : r + ship_len, c]
                
                # Invalid placement if it overlaps a Miss (-1)
                if np.any(segment == -1):
                    continue
                
                # Check for Hits
                num_hits = np.sum(segment == 1)
                
                # Calculate Weight
                if num_hits > 0:
                    weight = HIT_BONUS + (HIT_MULTIPLIER * num_hits)
                else:
                    weight = BASE_WEIGHT
                    
                # Add weight to map
                for i in range(ship_len):
                    if segment[i] == 0:
                        prob_map[r + i, c] += weight

    # Strategy Decision: Hunt vs Target
    max_prob = np.max(prob_map)
    
    # If the highest probability is below the hit bonus threshold, 
    # it means no valid placements overlap existing hits (or no hits exist).
    # We are in "Hunt Mode". Apply Parity (Checkerboard) optimization.
    if max_prob < HIT_BONUS:
        # Create a checkerboard mask (cells where r+c is even)
        # This reduces search space by 50% while guaranteeing we find the smallest ship (size 2).
        mask = np.zeros((ROWS, COLS), dtype=bool)
        for r in range(ROWS):
            for c in range(COLS):
                if (r + c) % 2 == 0:
                    mask[r, c] = True
        
        masked_map = prob_map * mask
        
        # Only apply mask if valid targets remain within the mask
        if np.max(masked_map) > 0:
            prob_map = masked_map

    # Final Selection
    if np.max(prob_map) == 0:
        # Fallback for rare edge cases (e.g. board almost full, logic boundary)
        # Pick a random unknown cell
        unknowns = np.argwhere(grid == 0)
        if len(unknowns) > 0:
            choice = unknowns[random.randint(0, len(unknowns) - 1)]
            return int(choice[0]), int(choice[1])
        return 0, 0 # Should not happen

    # Pick the cell with the absolute highest probability
    # argmax finds the flattened index of the max value
    target_idx = np.argmax(prob_map)
    target_r, target_c = np.unravel_index(target_idx, (ROWS, COLS))
    
    return int(target_r), int(target_c)
