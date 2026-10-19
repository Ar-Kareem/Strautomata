
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, check for any hits that need follow-up shots
    hit_cells = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hit_cells.append((i, j))
    
    # If we have hits, prioritize attacking around them
    if hit_cells:
        # Try to find adjacent unknown cells to the hits
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for i, j in hit_cells:
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                    return (ni, nj)
    
    # If no obvious follow-up shots, use checkerboard pattern
    # With preference for higher probability areas (center first)
    # We'll use two checkerboard patterns - even and odd sums
    # Try one, if exhausted, try the other
    patterns = [
        [(i, j) for i in range(10) for j in range(10) if (i + j) % 2 == 0 and board[i][j] == 0],
        [(i, j) for i in range(10) for j in range(10) if (i + j) % 2 == 1 and board[i][j] == 0]
    ]
    
    for pattern in patterns:
        if pattern:
            # Sort by distance from center to prioritize central shots
            pattern.sort(key=lambda pos: (pos[0]-4.5)**2 + (pos[1]-4.5)**2)
            return pattern[0]
    
    # Fallback - should never happen if game is valid
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    
    return (0, 0)  # should never reach here
