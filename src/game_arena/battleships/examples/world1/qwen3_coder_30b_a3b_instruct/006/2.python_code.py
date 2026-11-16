
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier handling
    board = np.array(board)
    rows, cols = board.shape
    
    # Find all unvisited cells (0s)
    unvisited = np.where(board == 0)
    unvisited_positions = list(zip(unvisited[0], unvisited[1]))
    
    # If no unvisited cells, return None (though this shouldn't happen in valid game state)
    if not unvisited_positions:
        # Find any random cell from all cells (this should not happen in practice, but just in case)
        return (random.randint(0, 9), random.randint(0, 9))
    
    # Find all hits (1s)
    hits = np.where(board == 1)
    hit_positions = list(zip(hits[0], hits[1]))
    
    # If we have hits, prioritize adjacent unvisited cells to hits
    if hit_positions:
        # Get all adjacent unvisited cells to hits
        adjacent_unvisited = set()
        
        for r, c in hit_positions:
            # Check all 4 adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                # Check if the adjacent cell is within bounds and unvisited (0)
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                    adjacent_unvisited.add((nr, nc))
        
        # If there are adjacent unvisited cells to hits, pick one
        if adjacent_unvisited:
            return random.choice(list(adjacent_unvisited))
    
    # Otherwise, pick a random unvisited cell
    return random.choice(unvisited_positions)
