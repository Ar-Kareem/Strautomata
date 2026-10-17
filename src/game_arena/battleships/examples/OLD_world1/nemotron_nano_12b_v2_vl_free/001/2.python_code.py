
import random
from typing import List

def policy(board: List[List[int]]) -> tuple[int, int]:
    # Generate all unknown cells (cells not yet fired at)
    candidates = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                candidates.append((i, j))
    
    # Check if there are any hits on the board to adjust strategy
    has_hits = any(1 in row for row in board)
    
    if not has_hits:
        # If no hits, start from the center of the grid (5,5) if available
        return (5, 5) if (5, 5) in candidates else candidates[0]
    
    # Sort candidates in row-major order to ensure deterministic behavior
    candidates_sorted = sorted(candidates)
    best_score = -1
    best_cell = None
    
    # Evaluate each candidate based on adjacent hits
    for cell in candidates_sorted:
        i, j = cell
        score = 0
        # Check all four neighboring cells
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + dx, j + dy
            if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 1:
                score += 1
        # Update the best cell if this cell has a higher score
        if score > best_score:
            best_score = score
            best_cell = cell
    
    return best_cell
