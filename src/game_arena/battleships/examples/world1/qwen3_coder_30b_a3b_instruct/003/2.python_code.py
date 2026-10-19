
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Find all unexplored cells (0s) and cells that are hits (1s)
    # Go through the board looking for any hits (1)
    hit_cells = []
    unexplored_adjacent = []
    
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hit_cells.append((i, j))
                # Check all 4 adjacent cells for unexplored ones (0)
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 10 and 0 <= nj < 10:
                        if board[ni][nj] == 0:
                            unexplored_adjacent.append((ni, nj))
    
    # If there are adjacent unexplored cells to hits, prioritize one of them
    if unexplored_adjacent:
        # Return the first one to keep it simple and deterministic
        return unexplored_adjacent[0]
    
    # If no hits have been registered, choose a random unexplored cell
    unexplored_cells = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unexplored_cells.append((i, j))
    
    # Return random unexplored cell if any exist
    if unexplored_cells:
        return random.choice(unexplored_cells)
    
    # This shouldn't happen in a valid game but just in case
    # Pick a random cell
    return (random.randint(0, 9), random.randint(0, 9))
