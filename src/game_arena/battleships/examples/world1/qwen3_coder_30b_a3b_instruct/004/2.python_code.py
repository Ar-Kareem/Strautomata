
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all unshot cells (0s)
    unshot_cells = []
    adjacent_to_hits = []
    
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unshot_cells.append((i, j))
                # Check if adjacent to a hit (1)
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 1:
                        adjacent_to_hits.append((i, j))
                        break  # Only need to know it's adjacent to one hit
    
    # If there are cells adjacent to hits, prioritize those
    if adjacent_to_hits:
        # Choose randomly from adjacent cells
        return random.choice(adjacent_to_hits)
    
    # Otherwise, choose randomly from all unshot cells
    if unshot_cells:
        return random.choice(unshot_cells)
    
    # Fallback - shouldn't happen in valid game
    # Find first unshot cell
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    
    # If somehow all cells are shot, return (0,0) - game should be over
    return (0, 0)
