
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Smart Battleship policy that combines random exploration with targeted ship hunting.

    Args:
        board: 10x10 grid representing known opponent cells (0: unknown, -1: miss, 1: hit).

    Returns:
        A legal (row, col) move as a tuple.
    """
    # Flatten the board to find all possible unknown cells (0)
    unknown_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]

    # If no hits detected, fire randomly
    if 1 not in [cell for row in board for cell in row]:
        return random.choice(unknown_cells)

    # Find all hit cells (1) to prioritize adjacent shots
    hit_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 1]

    # Generate candidate moves adjacent to hits (horizontally/vertically)
    candidates = []
    for (i, j) in hit_cells:
        # Check horizontal neighbors
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue  # Skip the hit cell itself
                ni, nj = i + di, j + dj
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                    candidates.append((ni, nj))

    # If no adjacent candidates (unlikely), fall back to random
    if not candidates:
        return random.choice(unknown_cells)

    # Select the best candidate based on ship length estimation
    # (Simplified: Just pick a random adjacent cell for efficiency)
    return random.choice(candidates)
