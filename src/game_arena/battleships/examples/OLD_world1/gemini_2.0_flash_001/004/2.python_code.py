
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses a target (row, col) based on the current board state.

    Args:
        board: A 10x10 list of lists representing the opponent's board.
               0: unknown, -1: miss, 1: hit

    Returns:
        A tuple (row, col) representing the coordinates of the target.
    """
    n = len(board)

    # Prioritize hitting near existing hits
    hit_targets = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                hit_targets.append((r, c))

    if hit_targets:
        random.shuffle(hit_targets) # Try hits in random order
        for r, c in hit_targets:
            neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            random.shuffle(neighbors)

            for nr, nc in neighbors:
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                    return (nr, nc)

    # If no hits nearby, hunt for potential ship locations
    potential_targets = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                potential_targets.append((r,c))

    if potential_targets:
       random.shuffle(potential_targets)
       return potential_targets[0]

    # If somehow we've shot at every cell, return a random valid location
    # (This should never happen in a standard battleship game)
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                return (r, c)

    # As a last resort, return (0,0). This should never happen in a valid game state.
    return (0, 0)
