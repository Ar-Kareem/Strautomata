
import numpy as np
from collections import defaultdict
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    n = len(board)
    
    # Find all cells that haven't been fired at yet
    unknown_cells = []
    hit_cells = []
    
    for i in range(n):
        for j in range(n):
            if board[i, j] == 0:
                unknown_cells.append((i, j))
            elif board[i, j] == 1:
                hit_cells.append((i, j))
    
    # If we have hit cells, try to find adjacent cells to continue the hunt
    if hit_cells:
        # Look for hits that are part of known ships (connected components)
        # Check if we can extend a hit sequence
        for row, col in hit_cells:
            # Check adjacent cells (up, down, left, right)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < n and 0 <= nc < n and board[nr, nc] == 0:
                    return (nr, nc)
    
    # If no hit cell has an adjacent unknown cell, pick a random unknown cell
    # but try to prioritize cells in areas that could contain ships
    if unknown_cells:
        # Strategy: look for patterns to prioritize likely ship locations
        # Try to avoid the borders - they're less likely to contain ships
        # since ships are placed fully on the board
        
        # Create a score matrix to bias toward center if possible
        scores = np.zeros((n, n))
        
        # For each unknown cell, calculate a score based on proximity to known hits
        # and how many adjacent unknown cells are there
        
        for i in range(n):
            for j in range(n):
                if board[i, j] == 0:  # Only score unknown cells
                    # Initialize score
                    score = 1.0
                    
                    # If the cell is adjacent to any hit, increase the score
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < n and 0 <= nj < n and board[ni, nj] == 1:
                            score += 2.0  # High priority
                    scores[i, j] = score
        
        # Find cell with highest score
        max_score = np.max(scores)
        if max_score > 1.0:
            # Get all cells with the highest score
            best_cells = list(zip(*np.where(scores == max_score)))
            # Return the first one (or a random one if multiple)
            return random.choice(best_cells)
        else:
            # No score-based preference, just return a random unknown cell
            return random.choice(unknown_cells)
    else:
        # This shouldn't happen since there should always be unknown cells
        # but we return a random cell just in case
        return (random.randint(0, n-1), random.randint(0, n-1))
