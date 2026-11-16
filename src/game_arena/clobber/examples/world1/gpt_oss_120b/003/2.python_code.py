
import random
from typing import List

# Directions: (delta_row, delta_col, label)
_DIRECTIONS = [
    (-1, 0, 'U'),  # Up
    (0, 1, 'R'),   # Right
    (1, 0, 'D'),   # Down
    (0, -1, 'L')   # Left
]

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Choose a legal Clobber move.

    Parameters
    ----------
    you : List[List[int]]
        5x6 board where 1 indicates my piece.
    opponent : List[List[int]]
        5x6 board where 1 indicates opponent's piece.

    Returns
    -------
    str
        Move encoded as "row,col,dir".
    """
    rows = len(you)          # should be 5
    cols = len(you[0])       # should be 6

    legal_moves = []

    for r in range(rows):
        for c in range(cols):
            if you[r][c] != 1:
                continue  # no my piece here
            for dr, dc, label in _DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if opponent[nr][nc] == 1:
                        legal_moves.append(f"{r},{c},{label}")

    # According to the problem statement, there is always at least one legal move.
    # If for some reason the list is empty (corrupted input), fall back to a safe default.
    if not legal_moves:
        raise ValueError("No legal moves found, but at least one was expected.")

    # Choose a move at random to add a bit of nondeterminism.
    return random.choice(legal_moves)
