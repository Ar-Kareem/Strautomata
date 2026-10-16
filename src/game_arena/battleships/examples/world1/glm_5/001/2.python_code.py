
import numpy as np


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Advanced Battleship AI using probability density targeting.
    
    Key strategies:
    1. Probability density: Count valid ship placements through each cell
    2. Active hit targeting: Heavily prioritize extending known ship hits
    3. Sunk ship avoidance: Ignore placements through inactive (sunk) hits
    4. Parity optimization: Slight preference for checkerboard pattern
    
    Args:
        board: 10x10 grid where 0=unknown, -1=miss, 1=hit
        
    Returns:
        Tuple (row, col) for the next shot
    """
    board = np.array(board, dtype=int)
    ships = [5, 4, 3, 3, 2]
    
    # Find active hits (hits with unknown neighbors = unsunk ships)
    active_hits = set()
    for r in range(10):
        for c in range(10):
            if board[r, c] == 1:
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr, nc] == 0:
                        active_hits.add((r, c))
                        break
    
    # Calculate probability density
    prob = np.zeros((10, 10), dtype=float)
    
    for ship_len in ships:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - ship_len + 1):
                cells = [(r, c + i) for i in range(ship_len)]
                _eval_placement(prob, board, cells, active_hits)
        
        # Vertical placements
        for r in range(10 - ship_len + 1):
            for c in range(10):
                cells = [(r + i, c) for i in range(ship_len)]
                _eval_placement(prob, board, cells, active_hits)
    
    # Parity bonus (checkerboard efficiency)
    for r in range(10):
        for c in range(10):
            if board[r, c] == 0 and (r + c) % 2 == 0:
                prob[r, c] += 0.5
    
    # Select best unknown cell
    unknown_mask = board == 0
    if not np.any(unknown_mask):
        return (0, 0)
    
    masked_prob = prob * unknown_mask
    if np.max(masked_prob) == 0:
        idx = np.argwhere(unknown_mask)[0]
        return (int(idx[0]), int(idx[1]))
    
    best = np.unravel_index(np.argmax(masked_prob), (10, 10))
    return (int(best[0]), int(best[1]))


def _eval_placement(prob: np.ndarray, board: np.ndarray, 
                    cells: list, active_hits: set) -> None:
    """Evaluate a ship placement and update probability density."""
    active_count = 0
    has_inactive = False
    
    for r, c in cells:
        val = board[r, c]
        if val == -1:
            return  # Blocked by miss
        if val == 1:
            if (r, c) in active_hits:
                active_count += 1
            else:
                has_inactive = True
    
    if has_inactive:
        return  # Invalid: goes through sunk ship
    
    # Weight scheme: hunt=1, extend hit=50, continue line=200
    if active_count == 0:
        weight = 1.0
    elif active_count == 1:
        weight = 50.0
    else:
        weight = 200.0
    
    for r, c in cells:
        if board[r, c] == 0:
            prob[r, c] += weight
