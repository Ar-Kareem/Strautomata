
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # First, check for any hits and prioritize adjacent cells (target phase)
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))

    if hits:
        # Target phase: prioritize adjacent cells to hits
        adjacent_cells = set()
        for (i, j) in hits:
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                    adjacent_cells.add((ni, nj))

        if adjacent_cells:
            # Choose a random adjacent cell to prioritize (could be optimized further)
            return random.choice(list(adjacent_cells))

    # Hunt phase: no hits, so use a heuristic to choose the next cell
    # We'll use a simple heuristic: prioritize cells in a checkerboard pattern starting from the center
    # This spreads out shots and increases the chance of hitting a ship
    # We'll generate all possible cells in a checkerboard pattern and pick the first available one
    checkerboard_cells = []
    for i in range(10):
        for j in range(10):
            if (i + j) % 2 == 0:  # Checkerboard pattern
                if board[i][j] == 0:
                    checkerboard_cells.append((i, j))

    if checkerboard_cells:
        # Sort by distance from center to prioritize central cells
        center = (5, 5)
        checkerboard_cells.sort(key=lambda x: (x[0] - center[0])**2 + (x[1] - center[1])**2)
        return checkerboard_cells[0]

    # If no checkerboard cells are available, fall back to any available cell
    available_cells = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                available_cells.append((i, j))

    if available_cells:
        return available_cells[0]

    # This should theoretically never happen since the game should end before all cells are exhausted
    return (0, 0)
