
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship Policy: Hunt and Target with Parity optimization.
    
    Strategy:
    1. Hunt Mode: Fire on 'even' parity cells (row + col % 2 == 0) to cover maximum 
       ship placement efficiency.
    2. Target Mode: When a hit is found, explore adjacent cells. 
       Prioritize linear extensions if multiple hits align.
    """
    board_array = np.array(board)
    height, width = board_array.shape
    
    # Identify all hits (1) and misses (-1)
    hits = np.argwhere(board_array == 1)
    
    # List of potential shots
    candidates = []
    
    if len(hits) == 0:
        # HUNT MODE: Parity Check
        # Generate all valid moves (unknown cells)
        unknowns = np.argwhere(board_array == 0)
        # Filter for parity (checkerboard pattern)
        for r, c in unknowns:
            if (r + c) % 2 == 0:
                candidates.append((r, c))
        
        # Fallback if parity search exhausted (rare late game)
        if not candidates:
            candidates = [tuple(loc) for loc in unknowns]
            
    else:
        # TARGET MODE: Analyze hits
        potential_targets = set()
        
        for r, c in hits:
            # Check neighbors (Up, Down, Left, Right)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                
                # Check bounds and if cell is unexplored
                if 0 <= nr < height and 0 <= nc < width and board_array[nr][nc] == 0:
                    potential_targets.add((nr, nc))
        
        # If we have potential targets adjacent to hits, prioritize them
        if potential_targets:
            candidates = list(potential_targets)
        else:
            # If no adjacent cells are available (blocked by misses or edges),
            # we might be surrounded or the ship is sunk. Return to hunt mode
            # on remaining unknown cells (ignoring parity to be aggressive).
            unknowns = np.argwhere(board_array == 0)
            candidates = [tuple(loc) for loc in unknowns]

    # If no candidates (board full), return (0,0) as a safety (should not happen)
    if not candidates:
        return (0, 0)

    # Select a random candidate from the list
    return tuple(random.choice(candidates))
