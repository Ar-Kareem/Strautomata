
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all unshot cells (0) and cells that are hits (1)
    unshot_cells = []
    hit_cells = []
    
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unshot_cells.append((i, j))
            elif board[i][j] == 1:
                hit_cells.append((i, j))
    
    # If there are any hit cells, try to fire adjacent to them first
    if hit_cells:
        # Get the last hit cell, and check its adjacent unshot cells
        # This is a simple heuristic: expand around last hit to sink ships
        # But to be more systematic:
        # Go through each unshot cell that is adjacent to a hit cell
        adjacent_unshot = []
        for hit_row, hit_col in hit_cells:
            # Check four adjacent cells (up, down, left, right)
            neighbors = [(hit_row-1, hit_col), (hit_row+1, hit_col), (hit_row, hit_col-1), (hit_row, hit_col+1)]
            for r, c in neighbors:
                if 0 <= r < 10 and 0 <= c < 10:
                    if board[r][c] == 0:
                        adjacent_unshot.append((r, c))
        
        # If adjacent unshot cells exist, pick one at random
        if adjacent_unshot:
            return random.choice(adjacent_unshot)
    
    # If no adjacency logic applies or no hits yet, shoot randomly at unshot cells
    if unshot_cells:
        return random.choice(unshot_cells)

    # Fallback (should rarely happen)
    # Pick any unshot cell (this is for safety; normally we won't get here)
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    
    # Should not reach here if board is valid, but for completeness
    raise ValueError("No valid cells to fire at")
