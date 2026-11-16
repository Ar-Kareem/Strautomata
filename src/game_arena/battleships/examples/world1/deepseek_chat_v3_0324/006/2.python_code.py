
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, collect all unknown cells (0) and hit cells (1)
    unknown_cells = []
    hit_cells = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unknown_cells.append((i, j))
            elif board[i][j] == 1:
                hit_cells.append((i, j))
    
    # If there are hit cells, prioritize their neighbors
    potential_targets = deque()
    for (i, j) in hit_cells:
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                potential_targets.append((ni, nj))
    
    # Remove duplicates and shuffle to avoid bias
    unique_targets = list(set(potential_targets))
    random.shuffle(unique_targets)
    
    # If there are potential targets around hits, return one
    if unique_targets:
        return unique_targets[0]
    
    # Otherwise, choose a random unknown cell
    return random.choice(unknown_cells)
