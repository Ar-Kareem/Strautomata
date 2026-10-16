
import numpy as np

def policy(board):
    """
    Returns the next optimal move (row, col) for Battleship.
    
    Args:
        board: 10x10 grid of integers (0=unknown, -1=miss, 1=hit)
    
    Returns:
        (row, col): Tuple of integers (0-9) representing the next shot.
    """
    # Track remaining ship lengths (all ships are assumed alive until sunk)
    remaining_ships = [5, 4, 3, 3, 2]
    
    # Calculate probability for each cell
    prob = np.zeros((10, 10))
    for length in remaining_ships:
        # Calculate possible ship placements
        for i in range(10 - length + 1):
            for j in range(10):
                # Horizontal placements
                if all(board[i + k][j] == 0 for k in range(length)):
                    prob[i:i+length, j] += 1
                # Vertical placements
                if all(board[i][j + k] == 0 for k in range(length)):
                    prob[i, j:j+length] += 1
    
    # Adjust probabilities based on hits and misses
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:  # Hit increases adjacent probabilities
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        prob[ni][nj] += 1
            elif board[i][j] == -1:  # Miss decreases probabilities
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        prob[ni][nj] -= 1
    
    # Normalize probabilities (avoid negative values)
    prob = np.clip(prob, 0, None)
    
    # Find best unknown cell
    unknown_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
    if not unknown_cells:
        return (0, 0)  # Fallback (shouldn't happen)
    
    # Select cell with highest probability
    best_cell = max(unknown_cells, key=lambda cell: prob[cell[0]][cell[1]])
    return best_cell
